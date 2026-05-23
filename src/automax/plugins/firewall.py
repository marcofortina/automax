# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux firewall management plugins for firewalld, UFW and nftables."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import upload_text_to_temp
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _state(params: Dict[str, Any]) -> str:
    state = str(params.get("state", "present"))
    if state not in {"present", "absent"}:
        raise PluginValidationError("state must be present or absent")
    return state


class FirewalldPortPlugin(BasePlugin):
    name = "firewalld.port"
    description = "Manage a firewalld port rule."
    required_params = ("port",)
    optional_params = ("protocol", "zone", "state", "permanent", "reload", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = _state(params)
        protocol = str(params.get("protocol", "tcp"))
        port_spec = f"{params['port']}/{protocol}"
        zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
        permanent = "--permanent " if bool(params.get("permanent", True)) else ""
        action = "add-port" if state == "present" else "remove-port"
        query = "query-port"
        expected = "0" if state == "present" else "1"
        command = (
            f"if {_sudo(params)}firewall-cmd {zone}{permanent}--{query}={quote(port_spec)} >/dev/null 2>&1; "
            f"then present=0; else present=1; fi; "
            f"if [ \"$present\" = {expected} ]; then true; "
            f"else {_sudo(params)}firewall-cmd {zone}{permanent}--{action}={quote(port_spec)} && echo {CHANGE_MARKER}; fi"
        )
        if bool(params.get("reload", False)):
            command += f"; {_sudo(params)}firewall-cmd --reload >/dev/null"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.port failed")


class FirewalldServicePlugin(BasePlugin):
    name = "firewalld.service"
    description = "Manage a firewalld service rule."
    required_params = ("service",)
    optional_params = ("zone", "state", "permanent", "reload", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = _state(params)
        zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
        permanent = "--permanent " if bool(params.get("permanent", True)) else ""
        action = "add-service" if state == "present" else "remove-service"
        expected = "0" if state == "present" else "1"
        command = (
            f"if {_sudo(params)}firewall-cmd {zone}{permanent}--query-service={quote(params['service'])} >/dev/null 2>&1; "
            f"then present=0; else present=1; fi; "
            f"if [ \"$present\" = {expected} ]; then true; "
            f"else {_sudo(params)}firewall-cmd {zone}{permanent}--{action}={quote(params['service'])} && echo {CHANGE_MARKER}; fi"
        )
        if bool(params.get("reload", False)):
            command += f"; {_sudo(params)}firewall-cmd --reload >/dev/null"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.service failed")


class FirewalldRichRulePlugin(BasePlugin):
    name = "firewalld.rich_rule"
    description = "Manage a firewalld rich rule."
    required_params = ("rich_rule",)
    optional_params = ("zone", "state", "permanent", "reload", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = _state(params)
        zone = f"--zone={quote(params['zone'])} " if params.get("zone") else ""
        permanent = "--permanent " if bool(params.get("permanent", True)) else ""
        action = "add-rich-rule" if state == "present" else "remove-rich-rule"
        expected = "0" if state == "present" else "1"
        command = (
            f"if {_sudo(params)}firewall-cmd {zone}{permanent}--query-rich-rule={quote(params['rich_rule'])} >/dev/null 2>&1; "
            f"then present=0; else present=1; fi; "
            f"if [ \"$present\" = {expected} ]; then true; "
            f"else {_sudo(params)}firewall-cmd {zone}{permanent}--{action}={quote(params['rich_rule'])} && echo {CHANGE_MARKER}; fi"
        )
        if bool(params.get("reload", False)):
            command += f"; {_sudo(params)}firewall-cmd --reload >/dev/null"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.rich_rule failed")


class FirewalldReloadPlugin(BasePlugin):
    name = "firewalld.reload"
    description = "Reload firewalld configuration."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, f"{_sudo(params)}firewall-cmd --reload && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="firewalld.reload failed")


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
        _state(params)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "present"))
        parts = [str(params["rule"])]
        if params.get("from"):
            parts.extend(["from", str(params["from"])])
        if params.get("to"):
            parts.extend(["to", str(params["to"])])
        if params.get("port"):
            parts.extend(["port", str(params["port"])])
        if params.get("protocol"):
            parts.extend(["proto", str(params["protocol"])])
        if params.get("comment"):
            parts.extend(["comment", str(params["comment"])])
        rule_args = " ".join(quote(part) for part in parts)
        grep_text = " ".join(parts[: min(len(parts), 6)])
        if state == "present":
            command = f"{_sudo(params)}ufw status | grep -F -- {quote(grep_text)} >/dev/null || {{ {_sudo(params)}ufw {rule_args} && echo {CHANGE_MARKER}; }}"
        else:
            command = f"{_sudo(params)}ufw status | grep -F -- {quote(grep_text)} >/dev/null && {{ {_sudo(params)}ufw --force delete {rule_args} && echo {CHANGE_MARKER}; }} || true"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ufw.rule failed")


class UfwStatusPlugin(BasePlugin):
    name = "ufw.status"
    description = "Read UFW status."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, f"{_sudo(params)}ufw status verbose")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="ufw.status failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"status": out})


class UfwEnablePlugin(BasePlugin):
    name = "ufw.enable"
    description = "Enable UFW when inactive."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = f"{_sudo(params)}ufw status | grep -qi '^Status: active' || {{ {_sudo(params)}ufw --force enable && echo {CHANGE_MARKER}; }}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ufw.enable failed")


class UfwDisablePlugin(BasePlugin):
    name = "ufw.disable"
    description = "Disable UFW when active."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = f"{_sudo(params)}ufw status | grep -qi '^Status: inactive' || {{ {_sudo(params)}ufw --force disable && echo {CHANGE_MARKER}; }}"
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
        rc, out, err = exec_remote(context, f"{_sudo(params)}nft -c -f {quote(remote_path)}; rm -f {quote(remote_path)}")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="nftables.validate failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class NftablesApplyPlugin(NftablesValidatePlugin):
    name = "nftables.apply"
    description = "Validate and apply nftables rules from inline content or a controller file."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        remote_path = self._upload(params, context)
        command = f"{_sudo(params)}nft -c -f {quote(remote_path)} && {_sudo(params)}nft -f {quote(remote_path)} && rm -f {quote(remote_path)} && echo {CHANGE_MARKER}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="nftables.apply failed")
