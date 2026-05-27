# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Network interface, route and DNS operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.linux_ops import ResolverConfigPlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_file_expr, shell_var_ref, tempfile_command, quote, result_from_remote, sudo_prefix



def _plan(path: str, before: str, after: str, kind: str) -> list[Dict[str, Any]]:
    diff = "".join(unified_diff([before + "\n"], [after + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (desired)"))
    return [{"path": path, "diff": diff, "kind": kind}]


_BACKENDS = {"runtime", "networkmanager", "systemd-networkd", "ifcfg"}


def _backend(params: Dict[str, Any]) -> str:
    backend = str(params.get("backend", "runtime"))
    if backend not in _BACKENDS:
        raise PluginValidationError("network backend must be runtime, networkmanager, systemd-networkd or ifcfg")
    return backend


def _persist(params: Dict[str, Any]) -> bool:
    return bool(params.get("persist", False))


def _backup_cmd(path: str, params: Dict[str, Any]) -> str:
    if not bool(params.get("backup", True)):
        return "true"
    return f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}"


def _write_file_cmd(path: str, content: str, mode: str, params: Dict[str, Any]) -> str:
    temp_var = "automax_net_tmp"
    temp = shell_var_ref(temp_var)
    return " && ".join([
        tempfile_command(temp_var, "net"),
        heredoc_to_file_expr(temp, content),
        _backup_cmd(path, params),
        f"{sudo_prefix(params, default=True)}install -D -m {mode} {temp} {quote(path)}",
        f"rm -f {temp}",
    ])


def _nmcli_connection(name: str) -> str:
    return quote(name)


def _networkd_interface_content(params: Dict[str, Any]) -> str:
    lines = ["# Managed by automax\n", "[Match]\n", f"Name={params['name']}\n\n", "[Network]\n"]
    if params.get("address"):
        lines.append(f"Address={params['address']}/{params['prefix']}\n")
    if params.get("gateway"):
        lines.append(f"Gateway={params['gateway']}\n")
    return "".join(lines)


def _ifcfg_interface_content(params: Dict[str, Any]) -> str:
    lines = ["# Managed by automax\n", f"DEVICE={params['name']}\n", "ONBOOT=yes\n"]
    if params.get("mtu"):
        lines.append(f"MTU={params['mtu']}\n")
    if params.get("address"):
        lines.extend(["BOOTPROTO=none\n", f"IPADDR={params['address']}\n", f"PREFIX={params['prefix']}\n"])
    else:
        lines.append("BOOTPROTO=none\n")
    return "".join(lines)


class NetworkInterfacePlugin(BasePlugin):
    name = "network.interface"
    description = "Apply runtime and optional persistent interface state/address configuration."
    required_params = ("name",)
    optional_params = ("state", "address", "prefix", "gateway", "mtu", "persist", "backend", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = f"interface={params['name']} state={params.get('state', 'up')} address={params.get('address', '')}/{params.get('prefix', '')} mtu={params.get('mtu', '')} backend={_backend(params)} persist={_persist(params)}"
        path = f"interface:{params['name']}"
        if _persist(params) and _backend(params) == "systemd-networkd":
            path = f"/etc/systemd/network/10-{params['name']}.network"
            desired = _networkd_interface_content(params)
        if _persist(params) and _backend(params) == "ifcfg":
            path = f"/etc/sysconfig/network-scripts/ifcfg-{params['name']}"
            desired = _ifcfg_interface_content(params)
        return _plan(path, "current network configuration", desired, "network-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        backend = _backend(params)
        sudo = sudo_prefix(params, default=True)
        name = quote(params["name"])
        commands = []
        if params.get("address") and not params.get("prefix"):
            raise PluginValidationError("network.interface requires prefix when address is set")
        if _persist(params) and backend == "networkmanager":
            nm = _nmcli_connection(str(params["name"]))
            commands.append(f"{sudo}nmcli connection show {nm} >/dev/null 2>&1 || {sudo}nmcli connection add type ethernet ifname {name} con-name {nm}")
            if params.get("address"):
                commands.append(f"{sudo}nmcli connection modify {nm} ipv4.addresses {quote(str(params['address']) + '/' + str(params['prefix']))} ipv4.method manual")
            if params.get("gateway"):
                commands.append(f"{sudo}nmcli connection modify {nm} ipv4.gateway {quote(params['gateway'])}")
            if params.get("mtu"):
                commands.append(f"{sudo}nmcli connection modify {nm} 802-3-ethernet.mtu {quote(params['mtu'])}")
            commands.append(f"{sudo}nmcli connection up {nm}")
            return commands
        if _persist(params) and backend == "systemd-networkd":
            commands.append(_write_file_cmd(f"/etc/systemd/network/10-{params['name']}.network", _networkd_interface_content(params), "0644", params))
            commands.append(f"{sudo}systemctl restart systemd-networkd")
            return commands
        if _persist(params) and backend == "ifcfg":
            commands.append(_write_file_cmd(f"/etc/sysconfig/network-scripts/ifcfg-{params['name']}", _ifcfg_interface_content(params), "0644", params))
            commands.append(f"{sudo}nmcli connection reload 2>/dev/null || {sudo}systemctl restart NetworkManager 2>/dev/null || true")
            return commands
        if params.get("mtu"):
            commands.append(f"{sudo}ip link set dev {name} mtu {quote(params['mtu'])}")
        if params.get("address"):
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
    description = "Ensure a runtime and optional persistent IP route is present or absent."
    required_params = ("dest",)
    optional_params = ("gateway", "dev", "table", "metric", "state", "persist", "backend", "backup", "backup_suffix", "sudo")
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
        if _persist(params):
            backend = _backend(params)
            if backend == "networkmanager":
                if not params.get("dev"):
                    raise PluginValidationError("network.route with NetworkManager persistence requires dev")
                return [f"{sudo_prefix(params, default=True)}nmcli connection modify {quote(params['dev'])} +ipv4.routes {quote(self._route(params))} && {sudo_prefix(params, default=True)}nmcli connection up {quote(params['dev'])}"]
            if backend == "systemd-networkd":
                dev = str(params.get("dev", "routes"))
                content = f"# Managed by automax\n[Route]\nDestination={params['dest']}\n" + (f"Gateway={params['gateway']}\n" if params.get("gateway") else "")
                return [_write_file_cmd(f"/etc/systemd/network/20-{dev}-route.network.d/automax-route.conf", content, "0644", params), f"{sudo_prefix(params, default=True)}systemctl restart systemd-networkd"]
            if backend == "ifcfg":
                if not params.get("dev"):
                    raise PluginValidationError("network.route with ifcfg persistence requires dev")
                return [_write_file_cmd(f"/etc/sysconfig/network-scripts/route-{params['dev']}", self._route(params) + "\n", "0644", params)]
        if state == "present":
            return [f"{sudo_prefix(params, default=True)}ip route replace {route}"]
        if state == "absent":
            return [f"{sudo_prefix(params, default=True)}ip route del {route} || true"]
        raise PluginValidationError("network.route state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="network.route failed")


class NetworkBondPlugin(BasePlugin):
    name = "network.bond"
    description = "Create or update a runtime and optional persistent Linux bonding interface."
    required_params = ("name", "interfaces")
    optional_params = ("mode", "miimon", "state", "persist", "backend", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(f"bond:{params['name']}", "current bond state", f"interfaces={params['interfaces']} mode={params.get('mode', 'active-backup')}", "network-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        interfaces = params["interfaces"] if isinstance(params["interfaces"], list) else [params["interfaces"]]
        sudo = sudo_prefix(params, default=True)
        name = quote(params["name"])
        mode = quote(params.get("mode", "active-backup"))
        miimon = quote(params.get("miimon", 100))
        if _persist(params) and _backend(params) == "networkmanager":
            commands = [f"{sudo}nmcli connection show {name} >/dev/null 2>&1 || {sudo}nmcli connection add type bond ifname {name} con-name {name} mode {mode}"]
            for iface in interfaces:
                commands.append(f"{sudo}nmcli connection add type ethernet slave-type bond ifname {quote(iface)} master {name} con-name {quote(str(params['name']) + '-' + str(iface))} 2>/dev/null || true")
            commands.append(f"{sudo}nmcli connection up {name}")
            return commands
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
    description = "Create or update a runtime and optional persistent VLAN interface."
    required_params = ("name", "parent", "vlan_id")
    optional_params = ("address", "prefix", "state", "persist", "backend", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(f"vlan:{params['name']}", "current VLAN state", f"parent={params['parent']} id={params['vlan_id']}", "network-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
        name = quote(params["name"])
        if _persist(params) and _backend(params) == "networkmanager":
            commands = [f"{sudo}nmcli connection show {name} >/dev/null 2>&1 || {sudo}nmcli connection add type vlan ifname {name} con-name {name} dev {quote(params['parent'])} id {quote(params['vlan_id'])}"]
            if params.get("address"):
                if not params.get("prefix"):
                    raise PluginValidationError("network.vlan requires prefix when address is set")
                commands.append(f"{sudo}nmcli connection modify {name} ipv4.addresses {quote(str(params['address']) + '/' + str(params['prefix']))} ipv4.method manual")
            commands.append(f"{sudo}nmcli connection up {name}")
            return commands
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


class NetworkBridgePlugin(BasePlugin):
    name = "network.bridge"
    description = "Create or remove a runtime Linux bridge and enslave interfaces."
    required_params = ("name",)
    optional_params = ("interfaces", "state", "stp", "mtu", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        sudo = sudo_prefix(params, default=True)
        name = quote(params["name"])
        if state == "absent":
            return [f"ip link show dev {name} >/dev/null 2>&1 && {{ {sudo}ip link set dev {name} down; {sudo}ip link delete {name} type bridge; }} || true"]
        if state != "present":
            raise PluginValidationError("network.bridge state must be present or absent")
        interfaces = params.get("interfaces") or []
        if isinstance(interfaces, str):
            interfaces = [interfaces]
        commands = [f"ip link show dev {name} >/dev/null 2>&1 || {sudo}ip link add name {name} type bridge"]
        if params.get("mtu"):
            commands.append(f"{sudo}ip link set dev {name} mtu {quote(params['mtu'])}")
        if params.get("stp") is not None:
            stp = "1" if bool(params.get("stp")) else "0"
            commands.append(f"{sudo}ip link set dev {name} type bridge stp_state {stp}")
        for iface in interfaces:
            commands.append(f"{sudo}ip link set dev {quote(iface)} master {name}")
        commands.append(f"{sudo}ip link set dev {name} up")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="network.bridge failed")


class NetworkLinkAssertPlugin(BasePlugin):
    name = "network.link_assert"
    description = "Assert that a network link exists and optionally has expected state or MTU."
    required_params = ("name",)
    optional_params = ("state", "mtu", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "network.link_assert is a read-only network link assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        name = quote(params["name"])
        commands = [f"ip link show dev {name}"]
        if params.get("state"):
            commands.append(f"ip -brief link show dev {name} | grep -w {quote(str(params['state']).upper())}")
        if params.get("mtu"):
            commands.append(f"ip link show dev {name} | grep -w 'mtu {params['mtu']}'")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="network.link_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class NetworkRouteAssertPlugin(BasePlugin):
    name = "network.route_assert"
    description = "Assert that a route exists with optional gateway, device, table or metric."
    required_params = ("dest",)
    optional_params = ("gateway", "dev", "table", "metric", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "network.route_assert is a read-only route assertion"

    def _route_text(self, params: Dict[str, Any]) -> str:
        parts = [str(params["dest"])]
        if params.get("gateway"):
            parts.extend(["via", str(params["gateway"])])
        if params.get("dev"):
            parts.extend(["dev", str(params["dev"])])
        if params.get("metric"):
            parts.extend(["metric", str(params["metric"])])
        return " ".join(parts)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        table = f" table {quote(params['table'])}" if params.get("table") else ""
        return [f"ip route show{table} {quote(params['dest'])} | grep -F -- {quote(self._route_text(params))}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="network.route_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class NetworkDnsAssertPlugin(BasePlugin):
    name = "network.dns_assert"
    description = "Assert resolver nameserver, search and option entries from /etc/resolv.conf."
    optional_params = ("nameservers", "search", "options", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "network.dns_assert is a read-only resolver assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        commands = ["test -r /etc/resolv.conf"]
        for ns in params.get("nameservers") or []:
            commands.append(f"grep -Eq '^nameserver[[:space:]]+{quote(ns)}($|[[:space:]])' /etc/resolv.conf")
        search_values = params.get("search") or []
        if search_values:
            commands.append(f"grep -Eq '^search .*{quote(' '.join(str(item) for item in search_values))}' /etc/resolv.conf")
        for option in params.get("options") or []:
            commands.append(f"grep -Eq '^options .*{quote(option)}' /etc/resolv.conf")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="network.dns_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class NetworkPortCheckPlugin(BasePlugin):
    name = "network.port_check"
    description = "Check TCP or UDP connectivity from the remote target."
    required_params = ("host", "port")
    optional_params = ("protocol", "timeout", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "network.port_check is a read-only connectivity check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        protocol = str(params.get("protocol", "tcp"))
        timeout = str(params.get("timeout", 5))
        udp = " -u" if protocol == "udp" else ""
        if protocol not in {"tcp", "udp"}:
            raise PluginValidationError("network.port_check protocol must be tcp or udp")
        return [f"nc -z{udp} -w {quote(timeout)} {quote(params['host'])} {quote(params['port'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="network.port_check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
