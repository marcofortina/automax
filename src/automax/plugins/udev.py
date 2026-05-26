# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote udev rule management plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_file, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", False)) else ""


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


class UdevRulePlugin(BasePlugin):
    """Install a udev rules file with optional pre-change backup."""

    name = "udev.rule"
    description = "Install a udev rules file from content or structured rule entries."
    required_params = ("path",)
    optional_params = ("content", "rules", "backup", "backup_suffix", "mode", "owner", "group", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _render_rules(params)

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        content = _render_rules(params)
        path = str(params["path"])
        diff = "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))
        return [{"path": path, "diff": diff, "kind": "unified"}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        content = _render_rules(params)
        sudo = _sudo(params)
        temp = "/tmp/automax-udev-rule.$$"
        path = str(params["path"])
        backup_suffix = str(params.get("backup_suffix", ".bak"))
        mode = str(params.get("mode", "0644"))
        commands = [heredoc_to_file(temp, content)]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + backup_suffix)}")
        commands.append(f"{sudo}install -m {quote(mode)} {temp} {quote(path)}")
        if params.get("owner") or params.get("group"):
            owner = str(params.get("owner", ""))
            group = str(params.get("group", ""))
            spec = f"{owner}:{group}" if group else owner
            commands.append(f"{sudo}chown {quote(spec)} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="udev.rule failed", data={"path": params["path"]})


class UdevReloadPlugin(BasePlugin):
    name = "udev.reload"
    description = "Reload udev rules."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "udev.reload reloads runtime udev rules and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{_sudo(params)}udevadm control --reload-rules"]

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
        command = f"{_sudo(params)}udevadm trigger"
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
