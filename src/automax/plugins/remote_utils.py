# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote shell helpers for SSH-backed plugins.
"""

from __future__ import annotations

import shlex
from typing import Any, Tuple

from automax.core.models import ExecutionContext, PluginResult


CHANGE_MARKER = "__AUTOMAX_CHANGED__"


def quote(value: Any) -> str:
    """Quote a value for POSIX shell usage."""
    return shlex.quote(str(value))


def apply_cwd(command: str, context: ExecutionContext, explicit_cwd: str | None = None) -> str:
    """Prefix a remote command with the current step working directory when set."""
    cwd = explicit_cwd or context.step_state.get("cwd")
    if not cwd:
        return command
    return f"cd {quote(cwd)} && {command}"


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
    _, stdout, stderr = context.ssh_client.exec_command(
        command,
        timeout=timeout if timeout is not None else context.command_timeout,
        get_pty=get_pty,
    )
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
