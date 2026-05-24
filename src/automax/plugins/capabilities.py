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


class ToolExistsPlugin(BasePlugin):
    name = "tool.exists"
    description = "Assert that one executable exists on the remote PATH."
    required_params = ("name",)
    optional_params = ("path",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "tool.exists is a read-only remote dependency check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path_prefix = f"PATH={quote(params['path'])}:$PATH " if params.get("path") else ""
        return [f"{path_prefix}command -v {quote(params['name'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message=f"missing required tool: {params['name']}")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"tool": params["name"], "path": out.strip()})


class ToolVersionAssertPlugin(BasePlugin):
    name = "tool.version_assert"
    description = "Assert that a remote tool version output contains or matches the expected value."
    required_params = ("name",)
    optional_params = ("version_arg", "contains", "regex")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not params.get("contains") and not params.get("regex"):
            raise PluginValidationError("tool.version_assert requires contains or regex")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "tool.version_assert is a read-only remote dependency check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        arg = str(params.get("version_arg", "--version"))
        command = f"{quote(params['name'])} {arg} 2>&1"
        if params.get("contains"):
            return [f"{command} | grep -F -- {quote(params['contains'])}"]
        return [f"{command} | grep -E -- {quote(params['regex'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message=f"version assertion failed for tool: {params['name']}")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"tool": params["name"], "version": out.strip()})


class CapabilityAssertPlugin(BasePlugin):
    name = "capability.assert"
    description = "Assert remote tools, paths and optional shell checks required by a job preflight."
    optional_params = ("tools", "paths", "commands", "path")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not (_as_list(params.get("tools")) or _as_list(params.get("paths")) or _as_list(params.get("commands"))):
            raise PluginValidationError("capability.assert requires tools, paths or commands")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "capability.assert is a read-only remote dependency preflight"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path_prefix = f"PATH={quote(params['path'])}:$PATH " if params.get("path") else ""
        commands = [f"{path_prefix}command -v {quote(tool)}" for tool in _as_list(params.get("tools"))]
        commands.extend(f"test -e {quote(path)}" for path in _as_list(params.get("paths")))
        commands.extend(_as_list(params.get("commands")))
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        missing: list[str] = []
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        for command in self.manual_commands(params, context):
            rc, out, err = exec_remote(context, command)
            stdout_parts.append(out)
            stderr_parts.append(err)
            if rc != 0:
                missing.append(command)
        stdout = "\n".join(part for part in stdout_parts if part)
        stderr = "\n".join(part for part in stderr_parts if part)
        if missing:
            return PluginResult.failure(rc=1, stdout=stdout, stderr=stderr, message="capability preflight failed", data={"failed": missing})
        return PluginResult.success(changed=False, rc=0, stdout=stdout, stderr=stderr, data={"checked": self.manual_commands(params, context)})


class PluginRequirementsPlugin(BasePlugin):
    name = "plugin.requirements"
    description = "Report remote tools required by one or more plugins without connecting to a target."
    optional_params = ("plugin", "plugins")
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not (params.get("plugin") or params.get("plugins")):
            raise PluginValidationError("plugin.requirements requires plugin or plugins")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "plugin.requirements is a local requirements report"

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
