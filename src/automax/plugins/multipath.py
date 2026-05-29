# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote Linux multipath helper plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



class MultipathStatusPlugin(BasePlugin):
    name = "storage.multipath.status"
    description = "Read multipath status and optionally assert a minimum path count."
    required_params: tuple[str, ...] = ()
    optional_params = ("name", "expect_paths", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.multipath.status is a read-only status/assertion plugin and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        name = f" {quote(params['name'])}" if params.get("name") else ""
        return [f"{sudo_prefix(params, default=False)}multipath -ll{name}".rstrip()]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.multipath.status failed")
        expected = params.get("expect_paths")
        if expected is not None:
            path_count = out.count(" active ready running") + out.count(" running")
            if path_count < int(expected):
                return PluginResult.failure(rc=1, stdout=out, stderr=err, message=f"multipath path count {path_count} < {expected}")
        return PluginResult.success(changed=False, stdout=out, stderr=err, data={"raw": out})


class MultipathReloadPlugin(BasePlugin):
    name = "storage.multipath.reload"
    description = "Reload multipath maps."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.multipath.reload refreshes runtime multipath maps and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=False)}multipath -r"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.multipath.reload failed")


class MultipathAddPlugin(BasePlugin):
    name = "storage.multipath.add"
    description = "Add one WWID to multipath and optionally reload maps."
    required_params = ("wwid",)
    optional_params = ("reload", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.multipath.add changes runtime multipath maps and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=False)
        commands = [f"{sudo}multipath -a {quote(params['wwid'])}"]
        if bool(params.get("reload", True)):
            commands.append(f"{sudo}multipath -r")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.multipath.add failed")


class MultipathFlushPlugin(BasePlugin):
    name = "storage.multipath.remove"
    description = "Remove one multipath map by name or one WWID from multipath bindings."
    required_params: tuple[str, ...] = ()
    optional_params = ("name", "wwid", "reload", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not params.get("name") and not params.get("wwid"):
            raise PluginValidationError("storage.multipath.remove requires name or wwid")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.multipath.remove changes runtime multipath maps and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=False)
        commands = []
        if params.get("name"):
            commands.append(f"{sudo}multipath -f {quote(params['name'])}")
        if params.get("wwid"):
            commands.append(f"{sudo}multipath -w {quote(params['wwid'])}")
        if bool(params.get("reload", False)):
            commands.append(f"{sudo}multipath -r")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.multipath.remove failed")
