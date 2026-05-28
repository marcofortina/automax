# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote udev rule management plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError, RenderedFileInstallMixin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



def _render_rules(params: Dict[str, Any]) -> str:
    if "content" in params:
        content = str(params["content"])
        return content if content.endswith("\n") else content + "\n"
    rules = params.get("rules")
    if not isinstance(rules, list) or not rules:
        raise PluginValidationError("udev.rule requires content or a non-empty rules list")
    lines = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise PluginValidationError("udev.rule rules entries must be mappings")
        match = rule.get("match", {}) or {}
        parts = []
        for key, value in sorted((match.get("env", {}) or {}).items()):
            parts.append(f'ENV{{{key}}}=="{value}"')
        for key, value in sorted((match.get("attrs", {}) or {}).items()):
            parts.append(f'ATTR{{{key}}}=="{value}"')
        if "kernel" in match:
            parts.append(f'KERNEL=="{match["kernel"]}"')
        if "subsystem" in match:
            parts.append(f'SUBSYSTEM=="{match["subsystem"]}"')
        if "symlink" in rule:
            parts.append(f'SYMLINK+="{rule["symlink"]}"')
        if "owner" in rule:
            parts.append(f'OWNER="{rule["owner"]}"')
        if "group" in rule:
            parts.append(f'GROUP="{rule["group"]}"')
        if "mode" in rule:
            parts.append(f'MODE="{rule["mode"]}"')
        if not parts:
            raise PluginValidationError("udev.rule generated an empty rule")
        lines.append(", ".join(parts))
    return "\n".join(lines) + "\n"


class UdevRulePlugin(RenderedFileInstallMixin, BasePlugin):
    """Install a udev rules file with optional pre-change backup."""

    name = "udev.rule"
    description = "Install a udev rules file from content or structured rule entries."
    required_params = ("path",)
    optional_params = ("content", "rules", "backup", "backup_suffix", "mode", "owner", "group", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "udev-rule"
    rendered_file_diff_kind = "unified"

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _render_rules(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return _render_rules(params)

    def rendered_file_sudo(self, params: Dict[str, Any]) -> str:
        from automax.plugins.remote_utils import sudo_prefix

        return sudo_prefix(params, default=False)

    def rendered_file_result_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"path": params["path"]}


class UdevReloadPlugin(BasePlugin):
    name = "udev.reload"
    description = "Reload udev rules."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "udev.reload reloads runtime udev rules and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=False)}udevadm control --reload-rules"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="udev.reload failed")


class UdevTriggerPlugin(BasePlugin):
    name = "udev.trigger"
    description = "Trigger udev events and optionally wait for settle."
    required_params: tuple[str, ...] = ()
    optional_params = ("subsystem", "action", "udev_settle", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "udev.trigger changes runtime udev device state and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        command = f"{sudo_prefix(params, default=False)}udevadm trigger"
        if params.get("subsystem"):
            command += f" --subsystem-match={quote(params['subsystem'])}"
        if params.get("action"):
            command += f" --action={quote(params['action'])}"
        commands = [command]
        if bool(params.get("udev_settle", True)):
            commands.append("udevadm settle")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="udev.trigger failed")


class UdevSettlePlugin(BasePlugin):
    name = "udev.settle"
    description = "Wait for the udev event queue to settle."
    required_params: tuple[str, ...] = ()
    optional_params = ("timeout",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "udev.settle waits for runtime udev state and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        command = "udevadm settle"
        if params.get("timeout") is not None:
            command += f" --timeout={quote(params['timeout'])}"
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err) if rc == 0 else PluginResult.failure(rc=rc, stdout=out, stderr=err, message="udev.settle failed")
