# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote chmod plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote, sudo_prefix


class FsChmodPlugin(BasePlugin):
    """Change remote file mode with idempotent non-recursive checks."""

    name = "fs.permission.mode.set"
    description = "Set remote file or directory mode."
    required_params = ("path", "mode")
    optional_params = ("recursive", "sudo", "cwd")
    opens_remote_session = True

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: chmod {params.get('mode')} {params.get('path')}",
            data={"params": params},
        )

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        path = quote(params["path"])
        mode = str(params["mode"])
        recursive = bool(params.get("recursive", False))
        sudo = sudo_prefix(params, default=False)
        chmod_flags = "-R " if recursive else ""
        chmod_cmd = f"{sudo}chmod {chmod_flags}{quote(mode)} {path}"
        if recursive:
            command = f"{chmod_cmd} && echo {CHANGE_MARKER}"
        else:
            command = (
                f"test -e {path} && test \"$(stat -c %a {path})\" = {quote(mode)} "
                f"|| {{ {chmod_cmd} && echo {CHANGE_MARKER}; }}"
            )
        return apply_cwd(command, context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.permission.mode.set failed",
            data={"path": params["path"], "mode": params["mode"]},
        )


class FsModeGetPlugin(BasePlugin):
    """Read a remote file or directory mode."""

    name = "fs.permission.mode.get"
    description = "Read remote file or directory mode."
    required_params = ("path",)
    optional_params = ("cwd",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [apply_cwd(f"stat -c %a {quote(params['path'])}", context, params.get("cwd"))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = self.manual_commands(params, context)[0]
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.permission.mode.get failed")
        mode = out.strip()
        return PluginResult.success(changed=False, rc=rc, stdout=out, data={"path": params["path"], "mode": mode})


class FsModeCheckPlugin(BasePlugin):
    """Check a remote file or directory mode without failing on mismatches."""

    name = "fs.permission.mode.check"
    description = "Check remote file or directory mode."
    required_params = ("path", "mode")
    optional_params = ("cwd",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [apply_cwd(f"test -e {quote(params['path'])} && stat -c %a {quote(params['path'])} || true", context, params.get("cwd"))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        path = quote(params["path"])
        command = apply_cwd(f"if test -e {path}; then stat -c %a {path}; else exit 10; fi", context, params.get("cwd"))
        rc, out, err = exec_remote(context, command)
        if rc == 10:
            return PluginResult.success(changed=False, rc=0, data={"path": params["path"], "mode": params["mode"], "exists": False, "matches": False})
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.permission.mode.check failed")
        current = out.strip()
        expected = str(params["mode"])
        return PluginResult.success(
            changed=False,
            rc=0,
            stdout=out,
            data={"path": params["path"], "mode": expected, "current_mode": current, "exists": True, "matches": current == expected},
        )
