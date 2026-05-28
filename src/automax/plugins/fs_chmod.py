# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote chmod macro plugin.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote


class FsChmodPlugin(BasePlugin):
    """Change remote file mode with idempotent non-recursive checks."""

    name = "fs.permission.mode"
    description = "Set remote file or directory mode."
    required_params = ("path", "mode")
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
        chmod_flags = "-R " if recursive else ""
        chmod_cmd = f"chmod {chmod_flags}{quote(mode)} {path}"
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
            message="fs.permission.mode failed",
            data={"path": params["path"], "mode": params["mode"]},
        )
