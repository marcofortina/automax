# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote capability and dependency preflight plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.capabilities import plugin_tools
from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import exec_remote, quote


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


class CapabilityAssertPlugin(BasePlugin):
    name = "os.capability.check"
    description = "Check remote tools, paths and optional shell checks required by a job preflight."
    optional_params = ("tools", "paths", "commands", "path")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not (_as_list(params.get("tools")) or _as_list(params.get("paths")) or _as_list(params.get("commands"))):
            raise PluginValidationError("os.capability.check requires tools, paths or commands")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "os.capability.check is a read-only remote dependency preflight"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path_prefix = f"PATH={quote(params['path'])}:$PATH " if params.get("path") else ""
        commands = [f"{path_prefix}command -v {quote(tool)}" for tool in _as_list(params.get("tools"))]
        commands.extend(f"test -e {quote(path)}" for path in _as_list(params.get("paths")))
        commands.extend(_as_list(params.get("commands")))
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        missing: list[str] = []
        errors: list[dict[str, Any]] = []
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        checked = self.manual_commands(params, context)
        for command in checked:
            rc, out, err = exec_remote(context, command)
            stdout_parts.append(out)
            stderr_parts.append(err)
            if rc == 1:
                missing.append(command)
            elif rc != 0:
                errors.append({"command": command, "rc": rc, "stderr": err})
        stdout = "\n".join(part for part in stdout_parts if part)
        stderr = "\n".join(part for part in stderr_parts if part)
        data = {"checked": checked, "failed": missing, "matches": not missing and not errors}
        if errors:
            data["errors"] = errors
            return PluginResult.failure(
                rc=errors[0]["rc"],
                stdout=stdout,
                stderr=stderr,
                message="os.capability.check failed with a technical command error",
                data=data,
            )
        return PluginResult.success(changed=False, rc=0, stdout=stdout, stderr=stderr, data=data)


class PluginRequirementsPlugin(BasePlugin):
    name = "automax.plugin.requirements"
    description = "Report remote tools required by one or more plugins without connecting to a target."
    optional_params = ("plugin", "plugins")
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not (params.get("plugin") or params.get("plugins")):
            raise PluginValidationError("automax.plugin.requirements requires plugin or plugins")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "automax.plugin.requirements is a local requirements report"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        tools = sorted({tool for plugin in self._plugins(params) for tool in plugin_tools(plugin)})
        return [f"command -v {tool}" for tool in tools]

    def _plugins(self, params: Dict[str, Any]) -> list[str]:
        names = _as_list(params.get("plugins"))
        if params.get("plugin"):
            names.append(str(params["plugin"]))
        return names

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        requirements = {plugin: list(plugin_tools(plugin)) for plugin in self._plugins(params)}
        return PluginResult.success(changed=False, data={"requirements": requirements})
