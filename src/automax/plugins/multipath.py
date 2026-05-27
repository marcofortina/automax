# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote Linux multipath helper plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



class MultipathStatusPlugin(BasePlugin):
    name = "multipath.status"
    description = "Read multipath status and optionally assert a minimum path count."
    required_params: tuple[str, ...] = ()
    optional_params = ("name", "expect_paths", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "multipath.status is a read-only status/assertion plugin and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        name = f" {quote(params['name'])}" if params.get("name") else ""
        return [f"{sudo_prefix(params, default=False)}multipath -ll{name}".rstrip()]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="multipath.status failed")
        expected = params.get("expect_paths")
        if expected is not None:
            path_count = out.count(" active ready running") + out.count(" running")
            if path_count < int(expected):
                return PluginResult.failure(rc=1, stdout=out, stderr=err, message=f"multipath path count {path_count} < {expected}")
        return PluginResult.success(changed=False, stdout=out, stderr=err, data={"raw": out})


class MultipathReloadPlugin(BasePlugin):
    name = "multipath.reload"
    description = "Reload multipath maps."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "multipath.reload refreshes runtime multipath maps and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=False)}multipath -r"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="multipath.reload failed")


class MultipathFlushPlugin(BasePlugin):
    name = "multipath.flush"
    description = "Flush one multipath map."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "multipath.flush changes runtime multipath maps and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=False)}multipath -f {quote(params['name'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="multipath.flush failed")
