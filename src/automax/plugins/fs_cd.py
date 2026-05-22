# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote working-directory macro plugin.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import exec_remote, quote


class FsCdPlugin(BasePlugin):
    """Set the current step working directory for later remote substeps."""

    name = "fs.cd"
    description = "Set current remote working directory for the active step."
    required_params = ("path",)
    opens_remote_session = True

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        context.step_state["cwd"] = str(params.get("path"))
        return PluginResult.success(
            changed=False,
            message=f"dry-run: set remote cwd to {params.get('path')}",
            data={"cwd": params.get("path")},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        path = str(params["path"])
        quoted_path = quote(path)
        if params.get("create", False):
            command = f"mkdir -p {quoted_path} && test -d {quoted_path}"
        elif params.get("must_exist", True):
            command = f"test -d {quoted_path}"
        else:
            command = "true"
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(
                rc=rc,
                stdout=out,
                stderr=err,
                message=f"remote directory does not exist: {path}",
            )
        context.step_state["cwd"] = path
        return PluginResult.success(changed=False, data={"cwd": path})
