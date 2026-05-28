# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""sudo and sudoers management plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, ReadOnlyCommandPlugin, RenderedFileInstallMixin
from automax.plugins.remote_utils import exec_remote, quote, sudo_prefix



def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class SudoRulePlugin(RenderedFileInstallMixin, BasePlugin):
    name = "sudo.rule"
    description = "Install a structured sudoers.d rule with visudo validation, backup and safe mode."
    required_params = ("name", "subject")
    optional_params = ("hosts", "runas", "commands", "nopassword", "path", "backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "sudoers"
    rendered_file_diff_kind = "sudo-rule-plan"
    rendered_file_default_mode = "0440"

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", f"/etc/sudoers.d/{params['name']}"))

    def _content(self, params: Dict[str, Any]) -> str:
        subject = str(params["subject"])
        hosts = str(params.get("hosts", "ALL"))
        runas = str(params.get("runas", "ALL"))
        commands = params.get("commands", "ALL")
        if isinstance(commands, list):
            commands = ", ".join(str(item) for item in commands)
        tag = "NOPASSWD: " if bool(params.get("nopassword", False)) else ""
        return f"# Managed by automax\n{subject} {hosts}=({runas}) {tag}{commands}\n"

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._content(params)

    def rendered_file_validate_commands(self, params: Dict[str, Any], context: ExecutionContext, temp_path: str) -> list[str]:
        return [f"{self.rendered_file_sudo(params)}visudo -cf {temp_path}"]


class SudoValidatePlugin(ReadOnlyCommandPlugin):
    name = "sudo.validate"
    description = "Validate sudoers syntax with visudo without changing files."
    optional_params = ("path", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "sudo.validate is read-only validation and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        path = str(params.get("path", "/etc/sudoers"))
        return [f"{sudo_prefix(params, default=True)}visudo -cf {quote(path)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="sudo.validate failed")
        return PluginResult.success(changed=False, stdout=out, stderr=err)
