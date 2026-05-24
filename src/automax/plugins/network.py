# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Network interface, route and DNS operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.linux_ops import ResolverConfigPlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _plan(path: str, before: str, after: str, kind: str) -> list[Dict[str, Any]]:
    diff = "".join(unified_diff([before + "\n"], [after + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (desired)"))
    return [{"path": path, "diff": diff, "kind": kind}]


class NetworkInterfacePlugin(BasePlugin):
    name = "network.interface"
    description = "Apply runtime interface state and optional address configuration with iproute2."
    required_params = ("name",)
    optional_params = ("state", "address", "prefix", "mtu", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = f"interface={params['name']} state={params.get('state', 'up')} address={params.get('address', '')}/{params.get('prefix', '')} mtu={params.get('mtu', '')}"
        return _plan(f"interface:{params['name']}", "current runtime interface state", desired, "network-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        name = quote(params["name"])
        commands = []
        if params.get("mtu"):
            commands.append(f"{sudo}ip link set dev {name} mtu {quote(params['mtu'])}")
        if params.get("address"):
            if not params.get("prefix"):
                raise PluginValidationError("network.interface requires prefix when address is set")
            commands.append(f"{sudo}ip addr replace {quote(str(params['address']) + '/' + str(params['prefix']))} dev {name}")
        state = str(params.get("state", "up"))
        if state in {"up", "down"}:
            commands.append(f"{sudo}ip link set dev {name} {state}")
        else:
            raise PluginValidationError("network.interface state must be up or down")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="network.interface failed")


class NetworkRoutePlugin(BasePlugin):
    name = "network.route"
    description = "Ensure a runtime IP route is present or absent."
    required_params = ("dest",)
    optional_params = ("gateway", "dev", "table", "metric", "state", "sudo")
    opens_remote_session = True

    def _route_parts(self, params: Dict[str, Any]) -> list[str]:
        parts = [str(params["dest"])]
        if params.get("gateway"):
            parts.extend(["via", str(params["gateway"])])
        if params.get("dev"):
            parts.extend(["dev", str(params["dev"])])
        if params.get("metric"):
            parts.extend(["metric", str(params["metric"])])
        if params.get("table"):
            parts.extend(["table", str(params["table"])])
        return parts

    def _route(self, params: Dict[str, Any]) -> str:
        return " ".join(self._route_parts(params))

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        state = str(params.get("state", "present"))
        return _plan("routes", "current runtime routes", f"{state}: {self._route(params)}", "network-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        route = " ".join(quote(item) for item in self._route_parts(params))
        if state == "present":
            return [f"{_sudo(params)}ip route replace {route}"]
        if state == "absent":
            return [f"{_sudo(params)}ip route del {route} || true"]
        raise PluginValidationError("network.route state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="network.route failed")


class NetworkBondPlugin(BasePlugin):
    name = "network.bond"
    description = "Create or update a runtime Linux bonding interface."
    required_params = ("name", "interfaces")
    optional_params = ("mode", "miimon", "state", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(f"bond:{params['name']}", "current bond state", f"interfaces={params['interfaces']} mode={params.get('mode', 'active-backup')}", "network-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        interfaces = params["interfaces"] if isinstance(params["interfaces"], list) else [params["interfaces"]]
        sudo = _sudo(params)
        name = quote(params["name"])
        mode = quote(params.get("mode", "active-backup"))
        miimon = quote(params.get("miimon", 100))
        commands = [f"{sudo}modprobe bonding", f"test -d /sys/class/net/{name} || {sudo}ip link add {name} type bond", f"{sudo}ip link set {name} type bond mode {mode} miimon {miimon}"]
        for iface in interfaces:
            commands.extend([f"{sudo}ip link set {quote(iface)} down", f"{sudo}ip link set {quote(iface)} master {name}"])
        commands.append(f"{sudo}ip link set {name} {quote(params.get('state', 'up'))}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="network.bond failed")


class NetworkVlanPlugin(BasePlugin):
    name = "network.vlan"
    description = "Create or update a runtime VLAN interface."
    required_params = ("name", "parent", "vlan_id")
    optional_params = ("address", "prefix", "state", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(f"vlan:{params['name']}", "current VLAN state", f"parent={params['parent']} id={params['vlan_id']}", "network-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        name = quote(params["name"])
        commands = [f"test -d /sys/class/net/{name} || {sudo}ip link add link {quote(params['parent'])} name {name} type vlan id {quote(params['vlan_id'])}"]
        if params.get("address"):
            if not params.get("prefix"):
                raise PluginValidationError("network.vlan requires prefix when address is set")
            commands.append(f"{sudo}ip addr replace {quote(str(params['address']) + '/' + str(params['prefix']))} dev {name}")
        commands.append(f"{sudo}ip link set dev {name} {quote(params.get('state', 'up'))}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="network.vlan failed")


class NetworkDnsPlugin(ResolverConfigPlugin):
    name = "network.dns"
    description = "Configure DNS resolver settings using the backend-aware resolver implementation."
