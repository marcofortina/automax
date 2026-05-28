# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""auditd rule, status and reload plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError, ReadOnlyCommandPlugin, RenderedFileInstallMixin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, result_from_remote, sudo_prefix



def _rules(params: Dict[str, Any]) -> list[str]:
    raw = params.get("rules") or params.get("rule")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    raise PluginValidationError("auditd.rule requires rule or rules")


class AuditdRulePlugin(RenderedFileInstallMixin, BasePlugin):
    name = "auditd.rule"
    description = "Install an auditd rules.d drop-in with backup and optional reload."
    required_params = ("name",)
    optional_params = ("rule", "rules", "path", "backup", "backup_suffix", "reload", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "auditd"
    rendered_file_diff_kind = "auditd-plan"
    rendered_file_default_mode = "0640"

    def _path(self, params: Dict[str, Any]) -> str:
        name = str(params["name"])
        if not name.endswith(".rules"):
            name += ".rules"
        return str(params.get("path", f"/etc/audit/rules.d/{name}"))

    def _content(self, params: Dict[str, Any]) -> str:
        return "# Managed by automax\n" + "\n".join(_rules(params)) + "\n"

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._content(params)

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if not bool(params.get("reload", True)):
            return []
        sudo = self.rendered_file_sudo(params)
        return [f"if command -v augenrules >/dev/null 2>&1; then {sudo}augenrules --load; else {sudo}service auditd restart; fi"]


class AuditdStatusPlugin(ReadOnlyCommandPlugin):
    name = "auditd.status"
    description = "Read auditd status without changing the system."
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=True)}auditctl -s"]


class AuditdReloadPlugin(BasePlugin):
    name = "auditd.reload"
    description = "Reload auditd rules using augenrules or the auditd service."
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "auditd.reload is a runtime reload operation with no deterministic file diff"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"if command -v augenrules >/dev/null 2>&1; then {sudo_prefix(params, default=True)}augenrules --load; else {sudo_prefix(params, default=True)}service auditd restart; fi"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="auditd.reload failed")
