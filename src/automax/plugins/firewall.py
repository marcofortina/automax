# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux firewall management plugins for firewalld, UFW and nftables."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import upload_text_to_temp
from automax.plugins.remote_utils import cleanup_trap_command, CHANGE_MARKER, exec_remote, quote, result_from_remote, shell_var_ref, sudo_prefix, tempfile_command



def _state(params: Dict[str, Any]) -> str:
    state = str(params.get("state", "present"))
    if state not in {"present", "absent"}:
        raise PluginValidationError("state must be present or absent")
    return state


def _firewalld_scope(params: Dict[str, Any]) -> str:
    if bool(params.get("runtime", False)):
        return ""
    return "--permanent " if bool(params.get("permanent", True)) else ""


def _reload_command(params: Dict[str, Any]) -> str:
    mode = str(params.get("reload_mode", "reload" if bool(params.get("reload", False)) else "none"))
    if mode == "none":
        return ""
    if mode == "reload":
        return f"; {sudo_prefix(params, default=True)}firewall-cmd --reload >/dev/null"
    if mode == "complete-reload":
        return f"; {sudo_prefix(params, default=True)}firewall-cmd --complete-reload >/dev/null"
    raise PluginValidationError("reload_mode must be none, reload or complete-reload")


class FirewalldPortPlugin(BasePlugin):
    name = "firewalld.port"
    description = "Manage a firewalld port rule."
    required_params = ("port",)
    optional_params = ("protocol", "zone", "state", "permanent", "runtime", "reload", "reload_mode", "query_only", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = _state(params)
        protocol = str(params.get("protocol", "tcp"))
        port_spec = f"{params['port']}/{protocol}"
        zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
        permanent = _firewalld_scope(params)
        action = "add-port" if state == "present" else "remove-port"
        query = "query-port"
        expected = "0" if state == "present" else "1"
        command = (
            f"if {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{query}={quote(port_spec)} >/dev/null 2>&1; "
            f"then present=0; else present=1; fi; "
            f"if [ \"$present\" = {expected} ]; then true; "
            f"else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(port_spec)} && echo {CHANGE_MARKER}; fi"
        )
        if bool(params.get("query_only", False)):
            command = f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{query}={quote(port_spec)}"
        else:
            command += _reload_command(params)
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.port failed")


class FirewalldServicePlugin(BasePlugin):
    name = "firewalld.service"
    description = "Manage a firewalld service rule."
    required_params = ("service",)
    optional_params = ("zone", "state", "permanent", "runtime", "reload", "reload_mode", "query_only", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = _state(params)
        zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
        permanent = _firewalld_scope(params)
        action = "add-service" if state == "present" else "remove-service"
        expected = "0" if state == "present" else "1"
        command = (
            f"if {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-service={quote(params['service'])} >/dev/null 2>&1; "
            f"then present=0; else present=1; fi; "
            f"if [ \"$present\" = {expected} ]; then true; "
            f"else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(params['service'])} && echo {CHANGE_MARKER}; fi"
        )
        if bool(params.get("query_only", False)):
            command = f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-service={quote(params['service'])}"
        else:
            command += _reload_command(params)
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.service failed")


class FirewalldRichRulePlugin(BasePlugin):
    name = "firewalld.rich_rule"
    description = "Manage a firewalld rich rule."
    required_params = ("rich_rule",)
    optional_params = ("zone", "state", "permanent", "runtime", "reload", "reload_mode", "query_only", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = _state(params)
        zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
        permanent = _firewalld_scope(params)
        action = "add-rich-rule" if state == "present" else "remove-rich-rule"
        expected = "0" if state == "present" else "1"
        command = (
            f"if {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-rich-rule={quote(params['rich_rule'])} >/dev/null 2>&1; "
            f"then present=0; else present=1; fi; "
            f"if [ \"$present\" = {expected} ]; then true; "
            f"else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(params['rich_rule'])} && echo {CHANGE_MARKER}; fi"
        )
        if bool(params.get("query_only", False)):
            command = f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-rich-rule={quote(params['rich_rule'])}"
        else:
            command += _reload_command(params)
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.rich_rule failed")


class FirewalldReloadPlugin(BasePlugin):
    name = "firewalld.reload"
    description = "Reload firewalld configuration."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, f"{sudo_prefix(params, default=True)}firewall-cmd --reload && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.reload failed")


class FirewalldStatusPlugin(BasePlugin):
    name = "firewalld.status"
    description = "Read firewalld daemon state, default zone and active zones."
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "firewalld.status is a read-only firewall state query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = sudo_prefix(params, default=True)
        return [f"{sudo}firewall-cmd --state && {sudo}firewall-cmd --get-default-zone && {sudo}firewall-cmd --get-active-zones"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="firewalld.status failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"status": out})


class FirewalldListPlugin(BasePlugin):
    name = "firewalld.list"
    description = "List firewalld rules for one zone or all zones."
    optional_params = ("zone", "permanent", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "firewalld.list is a read-only firewall rule listing"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        permanent = " --permanent" if bool(params.get("permanent", False)) else ""
        zone = f" --zone={quote(params['zone'])}" if params.get("zone") else ""
        action = "--list-all" if params.get("zone") else "--list-all-zones"
        return [f"{sudo_prefix(params, default=True)}firewall-cmd{permanent}{zone} {action}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="firewalld.list failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"rules": out})


class FirewalldZonePlugin(FirewalldListPlugin):
    name = "firewalld.zone"
    description = "Read one firewalld zone configuration."
    required_params = ("zone",)
    optional_params = ("permanent", "sudo")


class UfwRulePlugin(BasePlugin):
    name = "ufw.rule"
    description = "Manage a UFW allow/deny/reject rule."
    required_params = ("rule",)
    optional_params = ("port", "protocol", "from", "to", "state", "comment", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if str(params["rule"]) not in {"allow", "deny", "reject", "limit"}:
            raise PluginValidationError("ufw.rule rule must be allow, deny, reject or limit")
        if params.get("protocol") and not params.get("port"):
            raise PluginValidationError("ufw.rule protocol requires port")
        _state(params)

    def _rule_parts(self, params: Dict[str, Any]) -> list[str]:
        parts = [str(params["rule"])]
        if params.get("from") or params.get("to"):
            parts.extend(["from", str(params.get("from") or "any")])
            parts.extend(["to", str(params.get("to") or "any")])
            if params.get("port"):
                parts.extend(["port", str(params["port"])])
                if params.get("protocol"):
                    parts.extend(["proto", str(params["protocol"])])
        elif params.get("port"):
            port = str(params["port"])
            protocol = params.get("protocol")
            parts.append(f"{port}/{protocol}" if protocol else port)
        if params.get("comment"):
            parts.extend(["comment", str(params["comment"])])
        return parts

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        rule_args = " ".join(quote(part) for part in self._rule_parts(params))
        if str(params.get("state", "present")) == "absent":
            return [f"{sudo_prefix(params, default=True)}ufw --force delete {rule_args}"]
        return [f"{sudo_prefix(params, default=True)}ufw {rule_args}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "present"))
        parts = self._rule_parts(params)
        rule_args = " ".join(quote(part) for part in parts)
        grep_text = " ".join(parts[: min(len(parts), 6)])
        if state == "present":
            command = f"{sudo_prefix(params, default=True)}ufw status | grep -F -- {quote(grep_text)} >/dev/null || {{ {sudo_prefix(params, default=True)}ufw {rule_args} && echo {CHANGE_MARKER}; }}"
        else:
            command = f"{sudo_prefix(params, default=True)}ufw status | grep -F -- {quote(grep_text)} >/dev/null && {{ {sudo_prefix(params, default=True)}ufw --force delete {rule_args} && echo {CHANGE_MARKER}; }} || true"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ufw.rule failed")


class UfwStatusPlugin(BasePlugin):
    name = "ufw.status"
    description = "Read UFW status."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, f"{sudo_prefix(params, default=True)}ufw status verbose")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="ufw.status failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"status": out})


class UfwEnablePlugin(BasePlugin):
    name = "ufw.enable"
    description = "Enable UFW when inactive."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = f"{sudo_prefix(params, default=True)}ufw status | grep -qi '^Status: active' || {{ {sudo_prefix(params, default=True)}ufw --force enable && echo {CHANGE_MARKER}; }}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ufw.enable failed")


class UfwDisablePlugin(BasePlugin):
    name = "ufw.disable"
    description = "Disable UFW when active."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = f"{sudo_prefix(params, default=True)}ufw status | grep -qi '^Status: inactive' || {{ {sudo_prefix(params, default=True)}ufw --force disable && echo {CHANGE_MARKER}; }}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ufw.disable failed")


class NftablesValidatePlugin(BasePlugin):
    name = "nftables.validate"
    description = "Validate nftables rules from inline content or a controller file."
    optional_params = ("content", "src", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        if bool(params.get("content")) == bool(params.get("src")):
            raise PluginValidationError("nftables.validate requires exactly one of content or src")

    def _upload(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        if params.get("src"):
            content = Path(str(params["src"])).expanduser().read_text(encoding="utf-8")
        else:
            content = str(params["content"])
        return upload_text_to_temp(context, content, encoding="utf-8")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        remote_path = self._upload(params, context)
        rc, out, err = exec_remote(context, f"{sudo_prefix(params, default=True)}nft -c -f {quote(remote_path)}; rm -f {quote(remote_path)}")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="nftables.validate failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class NftablesApplyPlugin(NftablesValidatePlugin):
    name = "nftables.apply"
    description = "Validate and apply nftables rules from inline content or a controller file."
    optional_params = ("content", "src", "backup_before", "persistent_file", "reload_service", "check_only", "sudo")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        remote_path = self._upload(params, context)
        sudo = sudo_prefix(params, default=True)
        commands = [f"{sudo}nft -c -f {quote(remote_path)}"]
        if not bool(params.get("check_only", False)):
            if bool(params.get("backup_before", False)):
                backup_var = "automax_nft_backup"
                commands.append(f"{tempfile_command(backup_var, 'nftables-backup', suffix='.nft')} && {cleanup_trap_command(backup_var)} && {sudo}nft list ruleset > {shell_var_ref(backup_var)}")
            commands.append(f"{sudo}nft -f {quote(remote_path)}")
            if params.get("persistent_file"):
                dest = str(params["persistent_file"])
                if bool(params.get("backup_before", False)):
                    commands.append(f"test ! -e {quote(dest)} || {sudo}cp -p {quote(dest)} {quote(dest + '.bak')}")
                commands.append(f"{sudo}install -D -m 0644 {quote(remote_path)} {quote(dest)}")
            if params.get("reload_service"):
                commands.append(f"{sudo}systemctl reload {quote(params['reload_service'])}")
            commands.append(f"echo {CHANGE_MARKER}")
        commands.append(f"rm -f {quote(remote_path)}")
        rc, out, err = exec_remote(context, " && ".join(commands))
        if bool(params.get("check_only", False)) and rc == 0:
            return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="nftables.apply failed")

class NftablesListPlugin(BasePlugin):
    name = "nftables.list"
    description = "List the active nftables ruleset or one table."
    optional_params = ("family", "table", "handle", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "nftables.list is a read-only ruleset query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        handle = " -a" if bool(params.get("handle", False)) else ""
        if params.get("table"):
            family = str(params.get("family", "inet"))
            return [f"{sudo_prefix(params, default=True)}nft{handle} list table {quote(family)} {quote(params['table'])}"]
        return [f"{sudo_prefix(params, default=True)}nft{handle} list ruleset"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="nftables.list failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"ruleset": out})


class NftablesExportPlugin(NftablesListPlugin):
    name = "nftables.export"
    description = "Export the active nftables ruleset to stdout or a remote file."
    optional_params = ("family", "table", "handle", "dest", "backup", "backup_suffix", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        command = super().manual_commands(params, context)[0]
        if not params.get("dest"):
            return [command]
        dest = str(params["dest"])
        sudo = sudo_prefix(params, default=True)
        commands = []
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(dest)} || {sudo}cp -p {quote(dest)} {quote(dest + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}mkdir -p $(dirname {quote(dest)})")
        commands.append(f"{command} | {sudo}tee {quote(dest)} >/dev/null")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="nftables.export failed")
        return PluginResult.success(changed=bool(params.get("dest")), rc=rc, stdout=out, stderr=err, data={"dest": params.get("dest")})


class IptablesRulePlugin(BasePlugin):
    name = "iptables.rule"
    description = "Ensure an iptables rule is present or absent in a table and chain."
    required_params = ("chain", "rule")
    optional_params = ("table", "state", "ipv6", "position", "comment", "wait", "save_after", "dest", "backup_before", "sudo")
    parameter_schema = {
        "wait": {
            "type": "integer",
            "default": None,
            "min": 0,
            "description": "iptables -w lock wait timeout in seconds.",
        }
    }
    opens_remote_session = True

    def _bin(self, params: Dict[str, Any]) -> str:
        return "ip6tables" if bool(params.get("ipv6", False)) else "iptables"

    def _table(self, params: Dict[str, Any]) -> str:
        return str(params.get("table", "filter"))

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "iptables.rule changes runtime firewall state; use manual commands for the exact rule operation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = _state(params)
        binary = self._bin(params)
        table = self._table(params)
        chain = str(params["chain"])
        rule = str(params["rule"])
        if params.get("comment") and "--comment" not in rule:
            rule = f"{rule} -m comment --comment {quote(params['comment'])}"
        sudo = sudo_prefix(params, default=True)
        wait = f" -w {quote(params['wait'])}" if params.get("wait") is not None else ""
        save_binary = "ip6tables-save" if bool(params.get("ipv6", False)) else "iptables-save"
        save_dest = str(params.get("dest") or ("/etc/iptables/rules.v6" if bool(params.get("ipv6", False)) else "/etc/iptables/rules.v4"))
        backup_var = "automax_iptables_backup"
        backup = f"{tempfile_command(backup_var, 'iptables-backup', suffix='.rules')} && {cleanup_trap_command(backup_var)} && {sudo}{save_binary} > {shell_var_ref(backup_var)} && " if bool(params.get("backup_before", False)) else ""
        save_after = f" && {sudo}mkdir -p $(dirname {quote(save_dest)}) && {sudo}{save_binary} > {quote(save_dest)}" if bool(params.get("save_after", False)) else ""
        check = f"{sudo}{binary}{wait} -t {quote(table)} -C {quote(chain)} {rule}"
        insert = f"-I {quote(chain)} {quote(params['position'])}" if params.get("position") else f"-A {quote(chain)}"
        if state == "present":
            return [f"{check} >/dev/null 2>&1 || {{ {backup}{sudo}{binary}{wait} -t {quote(table)} {insert} {rule}{save_after}; }}"]
        return [f"{check} >/dev/null 2>&1 && {{ {backup}{sudo}{binary}{wait} -t {quote(table)} -D {quote(chain)} {rule}{save_after}; }} || true"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="iptables.rule failed")

class IptablesSavePlugin(BasePlugin):
    name = "iptables.save"
    description = "Save current iptables or ip6tables rules to a persistent file."
    required_params = ("dest",)
    optional_params = ("ipv6", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "iptables.save writes the current kernel firewall ruleset to a file"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        binary = "ip6tables-save" if bool(params.get("ipv6", False)) else "iptables-save"
        dest = str(params["dest"])
        return [f"{sudo_prefix(params, default=True)}mkdir -p $(dirname {quote(dest)}) && {sudo_prefix(params, default=True)}{binary} | {sudo_prefix(params, default=True)}tee {quote(dest)} >/dev/null"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="iptables.save failed")

class IptablesRestorePlugin(BasePlugin):
    name = "iptables.restore"
    description = "Restore iptables or ip6tables rules from a ruleset file."
    required_params = ("src",)
    optional_params = ("confirm", "ipv6", "test_only", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if params.get("confirm") is not True and not bool(params.get("test_only", False)):
            raise PluginValidationError("iptables.restore requires confirm: true unless test_only=true")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "iptables.restore replaces runtime firewall state from an explicit ruleset file"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        binary = "ip6tables-restore" if bool(params.get("ipv6", False)) else "iptables-restore"
        test_flag = " --test" if bool(params.get("test_only", False)) else ""
        return [f"test -f {quote(params['src'])} && {sudo_prefix(params, default=True)}{binary}{test_flag} < {quote(params['src'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="iptables.restore failed")


class IptablesListPlugin(BasePlugin):
    name = "iptables.list"
    description = "List iptables or ip6tables rules for a table or chain."
    optional_params = ("table", "chain", "ipv6", "numeric", "verbose", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def _bin(self, params: Dict[str, Any]) -> str:
        return "ip6tables" if bool(params.get("ipv6", False)) else "iptables"

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "iptables.list is a read-only firewall rule listing"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        table = str(params.get("table", "filter"))
        if bool(params.get("numeric", True)) or bool(params.get("verbose", False)):
            parts = [f"{sudo_prefix(params, default=True)}{self._bin(params)}", "-t", quote(table), "-L"]
            if params.get("chain"):
                parts.append(quote(params["chain"]))
            if bool(params.get("numeric", True)):
                parts.append("-n")
            if bool(params.get("verbose", False)):
                parts.append("-v")
            return [" ".join(parts)]
        chain = f" {quote(params['chain'])}" if params.get("chain") else ""
        return [f"{sudo_prefix(params, default=True)}{self._bin(params)} -t {quote(table)} -S{chain}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="iptables.list failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"rules": out})


class IptablesPolicyPlugin(BasePlugin):
    name = "iptables.policy"
    description = "Read or set an iptables built-in chain default policy."
    required_params = ("chain",)
    optional_params = ("table", "policy", "ipv6", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def _bin(self, params: Dict[str, Any]) -> str:
        return "ip6tables" if bool(params.get("ipv6", False)) else "iptables"

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "iptables.policy reads or updates a chain default policy; use manual commands for the exact operation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        table = str(params.get("table", "filter"))
        chain = str(params["chain"])
        binary = self._bin(params)
        sudo = sudo_prefix(params, default=True)
        if not params.get("policy"):
            return [f"{sudo}{binary} -t {quote(table)} -S {quote(chain)} | sed -n '1p'"]
        policy = str(params["policy"]).upper()
        if policy not in {"ACCEPT", "DROP", "QUEUE", "RETURN"}:
            raise PluginValidationError("iptables.policy policy must be ACCEPT, DROP, QUEUE or RETURN")
        return [f"{sudo}{binary} -t {quote(table)} -S {quote(chain)} | grep -Fx -- {quote('-P ' + chain + ' ' + policy)} >/dev/null || {sudo}{binary} -t {quote(table)} -P {quote(chain)} {quote(policy)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = self.manual_commands(params, context)[0]
        marker = f" && echo {CHANGE_MARKER}" if params.get("policy") else ""
        rc, out, err = exec_remote(context, command + marker)
        if params.get("policy"):
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="iptables.policy failed")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="iptables.policy failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"policy": out.strip()})


class IptablesChainPlugin(BasePlugin):
    name = "iptables.chain"
    description = "Read one iptables or ip6tables chain."
    required_params = ("chain",)
    optional_params = ("table", "ipv6", "numeric", "verbose", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "iptables.chain is a read-only chain query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return IptablesListPlugin().manual_commands({**params, "chain": params["chain"]}, context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="iptables.chain failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"chain": out})



def _firewalld_port_manual(self: FirewalldPortPlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    self.validate(params)
    state = _state(params)
    protocol = str(params.get("protocol", "tcp"))
    port_spec = f"{params['port']}/{protocol}"
    zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
    permanent = _firewalld_scope(params)
    action = "add-port" if state == "present" else "remove-port"
    query = "query-port"
    expected = "0" if state == "present" else "1"
    if bool(params.get("query_only", False)):
        return [f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{query}={quote(port_spec)}"]
    command = (
        f"if {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{query}={quote(port_spec)} >/dev/null 2>&1; "
        f"then present=0; else present=1; fi; "
        f"if [ \"$present\" = {expected} ]; then true; "
        f"else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(port_spec)} && echo {CHANGE_MARKER}; fi"
    )
    return [command + _reload_command(params)]


def _firewalld_service_manual(self: FirewalldServicePlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    self.validate(params)
    state = _state(params)
    zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
    permanent = _firewalld_scope(params)
    action = "add-service" if state == "present" else "remove-service"
    expected = "0" if state == "present" else "1"
    if bool(params.get("query_only", False)):
        return [f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-service={quote(params['service'])}"]
    command = (
        f"if {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-service={quote(params['service'])} >/dev/null 2>&1; "
        f"then present=0; else present=1; fi; "
        f"if [ \"$present\" = {expected} ]; then true; "
        f"else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(params['service'])} && echo {CHANGE_MARKER}; fi"
    )
    return [command + _reload_command(params)]


def _firewalld_rich_rule_manual(self: FirewalldRichRulePlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    self.validate(params)
    state = _state(params)
    zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
    permanent = _firewalld_scope(params)
    action = "add-rich-rule" if state == "present" else "remove-rich-rule"
    expected = "0" if state == "present" else "1"
    if bool(params.get("query_only", False)):
        return [f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-rich-rule={quote(params['rich_rule'])}"]
    command = (
        f"if {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-rich-rule={quote(params['rich_rule'])} >/dev/null 2>&1; "
        f"then present=0; else present=1; fi; "
        f"if [ \"$present\" = {expected} ]; then true; "
        f"else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(params['rich_rule'])} && echo {CHANGE_MARKER}; fi"
    )
    return [command + _reload_command(params)]



class ExtendedFirewalldPortPlugin(FirewalldPortPlugin):
    """firewalld.port with query-only and reload-mode controls."""

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return _firewalld_port_manual(self, params, context)


class ExtendedFirewalldServicePlugin(FirewalldServicePlugin):
    """firewalld.service with query-only and reload-mode controls."""

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return _firewalld_service_manual(self, params, context)


class ExtendedFirewalldRichRulePlugin(FirewalldRichRulePlugin):
    """firewalld.rich_rule with query-only and reload-mode controls."""

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return _firewalld_rich_rule_manual(self, params, context)
