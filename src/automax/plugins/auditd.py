# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""auditd rule, status and reload plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import cleanup_trap_command, CHANGE_MARKER, exec_remote, heredoc_to_file_expr, shell_var_ref, tempfile_command, quote, result_from_remote, sudo_prefix



def _rules(params: Dict[str, Any]) -> list[str]:
    raw = params.get("rules") or params.get("rule")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    raise PluginValidationError("auditd.rule requires rule or rules")


class AuditdRulePlugin(BasePlugin):
    name = "auditd.rule"
    description = "Install an auditd rules.d drop-in with backup and optional reload."
    required_params = ("name",)
    optional_params = ("rule", "rules", "path", "backup", "backup_suffix", "reload", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        name = str(params["name"])
        if not name.endswith(".rules"):
            name += ".rules"
        return str(params.get("path", f"/etc/audit/rules.d/{name}"))

    def _content(self, params: Dict[str, Any]) -> str:
        return "# Managed by automax\n" + "\n".join(_rules(params)) + "\n"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        diff = "".join(unified_diff([], self._content(params).splitlines(keepends=True), fromfile=f"{self._path(params)} (current)", tofile=f"{self._path(params)} (desired)"))
        return [{"path": self._path(params), "kind": "auditd-plan", "diff": diff}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        content = self._content(params)
        path = self._path(params)
        sudo = sudo_prefix(params, default=True)
        temp_var = "automax_auditd_tmp"
        temp = shell_var_ref(temp_var)
        commands = [tempfile_command(temp_var, "auditd"), cleanup_trap_command(temp_var), heredoc_to_file_expr(temp, content)]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -D -m 0640 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        if bool(params.get("reload", True)):
            commands.append(f"if command -v augenrules >/dev/null 2>&1; then {sudo}augenrules --load; else {sudo}service auditd restart; fi")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="auditd.rule failed")


class AuditdStatusPlugin(BasePlugin):
    name = "auditd.status"
    description = "Read auditd status without changing the system."
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "auditd.status is read-only and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=True)}auditctl -s"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="auditd.status failed")
        return PluginResult.success(changed=False, stdout=out, stderr=err)


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
