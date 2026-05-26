# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote shell helpers for SSH-backed plugins.
"""

from __future__ import annotations

import re
import shlex
from typing import Any, Mapping, Tuple

from automax.plugins.base import PluginValidationError

from automax.core.models import ExecutionContext, PluginResult


CHANGE_MARKER = "__AUTOMAX_CHANGED__"
SUDO_NON_INTERACTIVE = "sudo -n"
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote(value: Any) -> str:
    """Quote a value for POSIX shell usage."""
    return shlex.quote(str(value))


def validate_env_name(name: Any) -> str:
    """Validate and normalize a POSIX shell environment variable name."""
    value = str(name)
    if not _ENV_NAME_RE.fullmatch(value):
        raise PluginValidationError(f"invalid environment variable name: {value!r}")
    return value


def normalize_env_mapping(env: Mapping[Any, Any]) -> dict[str, str]:
    """Return a string-only env mapping after validating all variable names."""
    return {validate_env_name(name): str(value) for name, value in env.items()}


def render_env_prefix(env: Mapping[Any, Any]) -> str:
    """Render a validated environment prefix for POSIX shell commands."""
    normalized = normalize_env_mapping(env)
    return " ".join(f"{name}={quote(value)}" for name, value in sorted(normalized.items()))


def _safe_heredoc_parts(content: Any, *, prefix: str) -> tuple[str, str]:
    text = str(content)
    delimiter = prefix
    used_lines = set(text.splitlines())
    counter = 0
    while delimiter in used_lines:
        counter += 1
        delimiter = f"{prefix}_{counter}"
    body = text if text.endswith("\n") else text + "\n"
    return delimiter, body


def heredoc_to_file(path: Any, content: Any, *, prefix: str = "AUTOMAX_EOF") -> str:
    """Render a safe quoted heredoc that writes content to path.

    The delimiter is selected so that content lines cannot terminate the heredoc early.
    """
    delimiter, body = _safe_heredoc_parts(content, prefix=prefix)
    return f"cat > {quote(path)} <<'{delimiter}'\n{body}{delimiter}"


def heredoc_to_stdin(command: str, content: Any, *, prefix: str = "AUTOMAX_EOF") -> str:
    """Render a safe quoted heredoc piped to a shell command."""
    delimiter, body = _safe_heredoc_parts(content, prefix=prefix)
    return f"cat <<'{delimiter}' | {command}\n{body}{delimiter}"


def apply_cwd(command: str, context: ExecutionContext, explicit_cwd: str | None = None) -> str:
    """Prefix a remote command with the current step environment and working directory."""
    env = context.step_state.get("env") or {}
    if env:
        if not isinstance(env, Mapping):
            raise PluginValidationError("step environment must be a mapping")
        command = f"{render_env_prefix(env)} {command}"
    cwd = explicit_cwd or context.step_state.get("cwd")
    if not cwd:
        return command
    return f"cd {quote(cwd)} && {command}"


def prepare_sudo_password_command(command: str, sudo_password: str | None) -> tuple[str, str | None]:
    """Wrap sudo -n commands so sudo can authenticate without consuming command stdin."""
    if not sudo_password or SUDO_NON_INTERACTIVE not in command:
        return command, None

    wrapped = f"""set +x
IFS= read -r automax_sudo_password
automax_sudo_passfile=$(mktemp /tmp/automax-sudo-pass.XXXXXX)
automax_sudo_askpass=$(mktemp /tmp/automax-sudo-askpass.XXXXXX)
trap 'rm -f "$automax_sudo_askpass" "$automax_sudo_passfile"' EXIT
printf '%s\n' "$automax_sudo_password" > "$automax_sudo_passfile"
unset automax_sudo_password
chmod 600 "$automax_sudo_passfile"
cat > "$automax_sudo_askpass" <<'__AUTOMAX_SUDO_ASKPASS__'
#!/bin/sh
cat "$AUTOMAX_SUDO_PASSFILE"
__AUTOMAX_SUDO_ASKPASS__
chmod 700 "$automax_sudo_askpass"
export AUTOMAX_SUDO_PASSFILE="$automax_sudo_passfile" SUDO_ASKPASS="$automax_sudo_askpass"
sudo() {{
    if [ "${{1:-}}" = "-n" ]; then
        shift
    fi
    command sudo -A -p '' "$@"
}}
{command}
"""
    return wrapped, f"{sudo_password}\n"


def exec_remote(
    context: ExecutionContext,
    command: str,
    *,
    timeout: int | None = None,
    get_pty: bool = False,
    encoding: str = "utf-8",
) -> Tuple[int, str, str]:
    """Execute a command through the active step-scoped SSH connection."""
    if context.ssh_client is None:
        raise RuntimeError("remote plugin requires an SSH session")
    command, sudo_stdin = prepare_sudo_password_command(command, context.sudo_password)
    stdin, stdout, stderr = context.ssh_client.exec_command(
        command,
        timeout=timeout if timeout is not None else context.command_timeout,
        get_pty=get_pty,
    )
    if sudo_stdin:
        stdin.write(sudo_stdin)
        stdin.channel.shutdown_write()
    rc = stdout.channel.recv_exit_status()
    out = stdout.read().decode(encoding, errors="replace")
    err = stderr.read().decode(encoding, errors="replace")
    return rc, out, err


def result_from_remote(
    *,
    rc: int,
    stdout: str,
    stderr: str,
    success_rc: int = 0,
    message: str,
    data: dict[str, Any] | None = None,
) -> PluginResult:
    """Build a PluginResult from a marker-based remote command."""
    changed = CHANGE_MARKER in stdout
    clean_stdout = stdout.replace(CHANGE_MARKER, "").strip()
    if rc != success_rc:
        return PluginResult.failure(rc=rc, stdout=clean_stdout, stderr=stderr, message=message)
    return PluginResult.success(
        changed=changed,
        rc=rc,
        stdout=clean_stdout,
        stderr=stderr,
        data=data or {},
    )
