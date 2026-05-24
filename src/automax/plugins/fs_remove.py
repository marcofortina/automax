# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote filesystem remove macro plugin.
"""

from __future__ import annotations

import posixpath
from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote


_ROOT_GUARD_PATHS = {
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/home",
    "/lib",
    "/lib64",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/srv",
    "/sys",
    "/tmp",
    "/usr",
    "/var",
}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def _clean_path(value: Any) -> str:
    raw = str(value).strip()
    if raw in {"", ".", ".."}:
        return raw
    if raw.startswith("/"):
        return posixpath.normpath(raw)
    return posixpath.normpath(raw)


def _is_same_or_child(path: str, prefix: str) -> bool:
    clean_path = _clean_path(path)
    clean_prefix = _clean_path(prefix)
    if clean_path == clean_prefix:
        return True
    return clean_path.startswith(clean_prefix.rstrip("/") + "/")


def _safe_label(path: str) -> str:
    label = _clean_path(path).strip("/").replace("/", "_")
    return label or "root"


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class FsRemovePlugin(BasePlugin):
    """Remove a remote file or directory idempotently with destructive-operation guardrails."""

    name = "fs.remove"
    description = "Remove a remote file or directory with optional backup, trash and path safety guards."
    required_params = ("path",)
    optional_params = (
        "recursive",
        "force",
        "confirm",
        "backup_before",
        "backup_path",
        "trash_dir",
        "max_depth",
        "allowlist",
        "denylist",
        "refuse_root_paths",
        "require_recursive_for_directories",
        "sudo",
        "cwd",
    )
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        path = _clean_path(params["path"])
        if path in {"", ".", ".."}:
            raise PluginValidationError("fs.remove path must not be empty, '.' or '..'")

        if bool(params.get("refuse_root_paths", True)) and path in _ROOT_GUARD_PATHS:
            raise PluginValidationError(f"fs.remove refuses protected root-level path: {path}")

        allowlist = _as_list(params.get("allowlist"))
        if allowlist and not any(_is_same_or_child(path, item) for item in allowlist):
            raise PluginValidationError("fs.remove path is outside the configured allowlist")

        denylist = _as_list(params.get("denylist"))
        if denylist and any(_is_same_or_child(path, item) for item in denylist):
            raise PluginValidationError("fs.remove path matches the configured denylist")

        if "max_depth" in params and params["max_depth"] is not None:
            try:
                max_depth = int(params["max_depth"])
            except (TypeError, ValueError) as exc:
                raise PluginValidationError("fs.remove max_depth must be an integer") from exc
            if max_depth < 0:
                raise PluginValidationError("fs.remove max_depth must be >= 0")

        dangerous = any(
            bool(params.get(name, False))
            for name in ("recursive", "force", "backup_before", "trash_dir")
        ) or not bool(params.get("refuse_root_paths", True))
        if dangerous and not bool(params.get("confirm", False)):
            raise PluginValidationError(
                "fs.remove requires confirm=true for recursive, force, backup_before, trash_dir or root-guard override"
            )

    def _sudo(self, params: Dict[str, Any]) -> str:
        return "sudo -n " if bool(params.get("sudo", False)) else ""

    def _guard_commands(self, params: Dict[str, Any]) -> list[str]:
        path = quote(params["path"])
        commands: list[str] = []
        if bool(params.get("require_recursive_for_directories", True)) and not bool(params.get("recursive", False)):
            commands.append(f"if [ -d {path} ]; then echo 'fs.remove refused: directory requires recursive=true' >&2; exit 1; fi")
        if params.get("max_depth") is not None:
            overflow_depth = int(params["max_depth"]) + 1
            commands.append(
                f"if [ -d {path} ] && [ -n \"$(find {path} -mindepth {overflow_depth} -print -quit 2>/dev/null)\" ]; then echo 'fs.remove refused: max_depth exceeded' >&2; exit 1; fi"
            )
        return commands

    def _backup_command(self, params: Dict[str, Any]) -> str:
        sudo = self._sudo(params)
        path = quote(params["path"])
        backup_path = str(params.get("backup_path") or f"/tmp/automax-remove-backup-{_safe_label(params['path'])}")
        backup = quote(backup_path)
        return f"test ! -e {backup} && {sudo}cp -a -- {path} {backup} || {{ echo 'fs.remove backup path already exists or backup failed' >&2; exit 1; }}"

    def _remove_or_trash_command(self, params: Dict[str, Any]) -> str:
        sudo = self._sudo(params)
        path = quote(params["path"])
        if params.get("trash_dir"):
            trash_dir = quote(params["trash_dir"])
            return (
                f"{sudo}mkdir -p -- {trash_dir} && "
                f"{sudo}mv -- {path} {trash_dir}/$(basename -- {path}).$(date +%Y%m%d%H%M%S)"
            )
        flags = []
        if bool(params.get("recursive", False)):
            flags.append("r")
        if bool(params.get("force", False)):
            flags.append("f")
        flag_text = f"-{''.join(flags)} " if flags else ""
        return f"{sudo}rm {flag_text}-- {path}"

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        self.validate(params)
        path = quote(params["path"])
        commands = self._guard_commands(params)
        if bool(params.get("backup_before", False)):
            commands.append(self._backup_command(params))
        commands.append(self._remove_or_trash_command(params))
        body = " && ".join(commands)
        command = f"test ! -e {path} || {{ {body} && echo {CHANGE_MARKER}; }}"
        return apply_cwd(command, context, params.get("cwd"))

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        plan = {
            "path": params["path"],
            "recursive": bool(params.get("recursive", False)),
            "force": bool(params.get("force", False)),
            "backup_before": bool(params.get("backup_before", False)),
            "trash_dir": params.get("trash_dir"),
            "max_depth": params.get("max_depth"),
            "allowlist": _as_list(params.get("allowlist")),
            "denylist": _as_list(params.get("denylist")),
        }
        content = "\n".join(f"{key}: {value}" for key, value in plan.items()) + "\n"
        return _diff(str(params["path"]), content, "remove-plan")

    def manual_commands(
        self, params: Dict[str, Any], context: ExecutionContext
    ) -> list[str]:
        return [self._command(params, context)]

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        return PluginResult.success(
            changed=False,
            message=f"dry-run: remove {params.get('path')}",
            data={"params": params, "commands": self.manual_commands(params, context)},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="fs.remove requires an SSH session")

        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.remove failed",
            data={"path": params["path"]},
        )
