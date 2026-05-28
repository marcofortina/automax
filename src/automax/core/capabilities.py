# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Job-scoped remote capability requirements."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable

from automax.core.os_detect import TargetOS


@dataclass(frozen=True)
class CapabilityRequirement:
    """Tools required by one selected plugin invocation."""

    plugin: str
    tools: tuple[str, ...]


EXACT_TOOL_REQUIREMENTS: Dict[str, tuple[str, ...]] = {
    "alternatives.get": ("update-alternatives",),
    "alternatives.list": ("update-alternatives",),
    "alternatives.set": ("update-alternatives",),
    "apparmor.complain": ("aa-complain",),
    "apparmor.disable": ("aa-disable",),
    "apparmor.enforce": ("aa-enforce",),
    "apparmor.parser_validate": ("apparmor_parser",),
    "apparmor.profile": ("apparmor_parser",),
    "apparmor.profile_assert": ("aa-status",),
    "apparmor.reload": ("apparmor_parser",),
    "apparmor.status": ("aa-status",),
    "auditd.backlog_assert": ("auditctl",),
    "auditd.reload": ("auditctl",),
    "auditd.rule": ("auditctl",),
    "auditd.rules_facts": ("auditctl",),
    "auditd.search": ("ausearch",),
    "auditd.status": ("auditctl",),
    "auditd.syscall": ("auditctl",),
    "auditd.watch": ("auditctl",),
    "backup.manifest": ("find", "sha256sum"),
    "backup.prune": ("find",),
    "backup.restore_verify": ("sha256sum",),
    "block.empty_assert": ("blkid",),
    "block.fs_assert": ("blkid",),
    "block.mountpoint_assert": ("findmnt",),
    "blkid.assert": ("blkid",),
    "cert.fingerprint": ("openssl",),
    "cert.install_ca_bundle": ("openssl",),
    "cert.issuer_assert": ("openssl",),
    "cert.matches_key": ("openssl",),
    "cert.san_assert": ("openssl",),
    "cert.self_signed": ("openssl",),
    "cert.subject_assert": ("openssl",),
    "cert.verify_chain": ("openssl",),
    "chrony.sources_assert": ("chronyc",),
    "chrony.tracking_assert": ("chronyc",),
    "cron.list": ("crontab",),
    "fstab.validate": ("findmnt",),
    "fs.acl": ("getfacl", "setfacl"),
    "fs.acl.assert": ("getfacl",),
    "fs.acl.get": ("getfacl",),
    "fs.acl.restore": ("setfacl",),
    "network.firewall.iptables.chain": ("iptables",),
    "network.firewall.iptables.counter_assert": ("iptables",),
    "network.firewall.iptables.delete": ("iptables",),
    "network.firewall.iptables.exists_assert": ("iptables",),
    "network.firewall.iptables.list": ("iptables",),
    "network.firewall.iptables.policy": ("iptables",),
    "network.firewall.iptables.restore": ("iptables-restore",),
    "network.firewall.iptables.rule": ("iptables",),
    "network.firewall.iptables.save": ("iptables-save",),
    "lvm.facts": ("pvs", "vgs", "lvs"),
    "lvm.lv_assert": ("lvs",),
    "lvm.lv_present": ("lvcreate", "lvs"),
    "lvm.lv_remove": ("lvremove",),
    "lvm.pv_present": ("pvcreate", "pvs"),
    "lvm.pv_remove": ("pvremove",),
    "lvm.vg_present": ("vgcreate", "vgs"),
    "lvm.vg_remove": ("vgremove",),
    "mount.assert": ("findmnt",),
    "mount.facts": ("findmnt",),
    "mount.options_assert": ("findmnt",),
    "network.connectivity.port_check": ("nc",),
    "network.link.bond": ("ip", "modprobe"),
    "network.link.bridge": ("ip",),
    "network.link.check": ("ip",),
    "network.link.facts": ("ip",),
    "network.link.interface": ("ip",),
    "network.link.vlan": ("ip",),
    "network.route.add": ("ip",),
    "network.route.check": ("ip",),
    "network.route.facts": ("ip",),
    "network.route.remove": ("ip",),
    "network.firewall.nftables.apply": ("nft",),
    "network.firewall.nftables.export": ("nft",),
    "network.firewall.nftables.list": ("nft",),
    "network.firewall.nftables.rollback_file": ("nft",),
    "network.firewall.nftables.ruleset_assert": ("nft",),
    "network.firewall.nftables.validate": ("nft",),
    "pam.validate": ("awk",),
    "pkg.pin": ("install",),
    "pkg.repo_priority": ("install",),
    "ssh.fingerprint": ("ssh-keygen",),
    "ssh.host_keygen": ("ssh-keygen",),
    "ssh.keygen": ("ssh-keygen",),
    "ssh.public_key": ("ssh-keygen",),
    "sshd.validate": ("sshd",),
    "sudo.can_run": ("sudo",),
    "sudo.list": ("sudo",),
    "sudo.validate": ("visudo",),
    "swap.status": ("swapon",),
    "sysctl.assert": ("sysctl",),
    "sysctl.facts": ("sysctl",),
    "sysctl.get": ("sysctl",),
    "sysctl.reload": ("sysctl",),
    "sysctl.set": ("sysctl",),
    "timedatectl.ntp": ("timedatectl",),
    "timedatectl.status": ("timedatectl",),
    "timedatectl.timezone": ("timedatectl",),
    "transfer.rsync": ("rsync",),
    "udev.facts": ("udevadm",),
    "udev.reload": ("udevadm",),
    "udev.settle": ("udevadm",),
    "udev.test": ("udevadm",),
    "udev.trigger": ("udevadm",),
    "udev.validate": ("udevadm",),
}

DEBIAN_TOOL_REQUIREMENTS: Dict[str, tuple[str, ...]] = {
    "pkg.clean": ("apt-get",),
    "pkg.hold": ("apt-mark",),
    "pkg.owner": ("dpkg-query",),
    "pkg.query": ("dpkg-query",),
    "pkg.unhold": ("apt-mark",),
    "pkg.verify": ("dpkg",),
    "pkg.version_assert": ("dpkg-query",),
    "pkg.update_cache": ("apt-get",),
    "pkg.install": ("apt-get", "dpkg-query"),
    "pkg.remove": ("apt-get", "dpkg-query"),
    "pkg.upgrade": ("apt-get",),
    "network.firewall.ufw.delete": ("ufw",),
    "network.firewall.ufw.disable": ("ufw",),
    "network.firewall.ufw.enable": ("ufw",),
    "network.firewall.ufw.reset": ("ufw",),
    "network.firewall.ufw.rule": ("ufw",),
    "network.firewall.ufw.status": ("ufw",),
}

RHEL_TOOL_REQUIREMENTS: Dict[str, tuple[str, ...]] = {
    "authselect.profile": ("authselect",),
    "kernel.boot_param": ("grubby",),
    "kernel.boot_param_absent": ("grubby",),
    "pam.authselect": ("authselect",),
    "pkg.clean": ("rpm",),
    "pkg.hold": ("rpm",),
    "pkg.owner": ("rpm",),
    "pkg.query": ("rpm",),
    "pkg.unhold": ("rpm",),
    "pkg.verify": ("rpm",),
    "pkg.version_assert": ("rpm",),
    "pkg.update_cache": ("rpm",),
    "pkg.install": ("rpm",),
    "pkg.remove": ("rpm",),
    "pkg.upgrade": ("rpm",),
}

PREFIX_TOOL_REQUIREMENTS: Dict[str, tuple[str, ...]] = {
    "archive.": ("tar", "unzip", "zip", "gzip"),
    "fs.attr": ("chattr",),
    "kernel.module.": ("modprobe", "lsmod"),
    "mount.": ("mount",),
    "process.": ("pgrep",),
    "systemctl.": ("systemctl",),
    "systemd.": ("systemctl",),
}

DEBIAN_PREFIX_TOOL_REQUIREMENTS: Dict[str, tuple[str, ...]] = {
    "apparmor.": ("apparmor_parser",),
    "network.firewall.ufw.": ("ufw",),
}

RHEL_PREFIX_TOOL_REQUIREMENTS: Dict[str, tuple[str, ...]] = {
    "network.firewall.firewalld.": ("firewall-cmd",),
    "selinux.": ("semanage",),
}

PARAM_TOOL_REQUIREMENTS: Dict[tuple[str, str], tuple[str, ...]] = {
    ("fs.write", "validate_command"): ("sh",),
    ("fs.template", "validate_command"): ("sh",),
    ("fs.line", "validate_command"): ("sh",),
    ("fs.replace", "validate_command"): ("sh",),
    ("archive.untar", "checksum"): ("sha256sum",),
    ("archive.unzip", "checksum"): ("sha256sum",),
}

DEBIAN_PACKAGES: Dict[str, str] = {
    "aa-complain": "apparmor-utils",
    "aa-disable": "apparmor-utils",
    "aa-enforce": "apparmor-utils",
    "aa-status": "apparmor-utils",
    "apparmor_parser": "apparmor",
    "apt-get": "apt",
    "apt-mark": "apt",
    "auditctl": "auditd",
    "ausearch": "auditd",
    "awk": "mawk",
    "blkid": "util-linux",
    "chattr": "e2fsprogs",
    "chronyc": "chrony",
    "crontab": "cron",
    "curl": "curl",
    "dpkg": "dpkg",
    "dpkg-query": "dpkg",
    "find": "findutils",
    "findmnt": "util-linux",
    "getfacl": "acl",
    "gzip": "gzip",
    "install": "coreutils",
    "ip6tables": "iptables",
    "iptables": "iptables",
    "iptables-restore": "iptables",
    "iptables-save": "iptables",
    "ip": "iproute2",
    "lsmod": "kmod",
    "lvcreate": "lvm2",
    "lvremove": "lvm2",
    "lvs": "lvm2",
    "modprobe": "kmod",
    "mount": "mount",
    "nc": "netcat-openbsd",
    "nft": "nftables",
    "openssl": "openssl",
    "pgrep": "procps",
    "pvcreate": "lvm2",
    "pvremove": "lvm2",
    "pvs": "lvm2",
    "rsync": "rsync",
    "setfacl": "acl",
    "sha256sum": "coreutils",
    "ssh-keygen": "openssh-client",
    "sshd": "openssh-server",
    "sudo": "sudo",
    "swapon": "util-linux",
    "sysctl": "procps",
    "systemctl": "systemd",
    "tar": "tar",
    "timedatectl": "systemd",
    "udevadm": "udev",
    "ufw": "ufw",
    "unzip": "unzip",
    "update-alternatives": "dpkg",
    "vgcreate": "lvm2",
    "vgremove": "lvm2",
    "vgs": "lvm2",
    "visudo": "sudo",
    "zip": "zip",
}

RHEL_PACKAGES: Dict[str, str] = {
    "auditctl": "audit",
    "ausearch": "audit",
    "authselect": "authselect",
    "awk": "gawk",
    "blkid": "util-linux",
    "chattr": "e2fsprogs",
    "chronyc": "chrony",
    "crontab": "cronie",
    "curl": "curl",
    "dnf": "dnf",
    "firewall-cmd": "firewalld",
    "find": "findutils",
    "findmnt": "util-linux",
    "getfacl": "acl",
    "grubby": "grubby",
    "gzip": "gzip",
    "install": "coreutils",
    "ip6tables": "iptables",
    "iptables": "iptables",
    "iptables-restore": "iptables",
    "iptables-save": "iptables",
    "ip": "iproute",
    "lsmod": "kmod",
    "lvcreate": "lvm2",
    "lvremove": "lvm2",
    "lvs": "lvm2",
    "modprobe": "kmod",
    "mount": "util-linux",
    "nc": "nmap-ncat",
    "nft": "nftables",
    "openssl": "openssl",
    "pgrep": "procps-ng",
    "pvcreate": "lvm2",
    "pvremove": "lvm2",
    "pvs": "lvm2",
    "restorecon": "policycoreutils",
    "rpm": "rpm",
    "rsync": "rsync",
    "semanage": "policycoreutils-python-utils",
    "setfacl": "acl",
    "sha256sum": "coreutils",
    "ssh-keygen": "openssh-clients",
    "sshd": "openssh-server",
    "sudo": "sudo",
    "swapon": "util-linux",
    "sysctl": "procps-ng",
    "systemctl": "systemd",
    "tar": "tar",
    "timedatectl": "systemd",
    "udevadm": "systemd-udev",
    "unzip": "unzip",
    "update-alternatives": "chkconfig",
    "vgcreate": "lvm2",
    "vgremove": "lvm2",
    "vgs": "lvm2",
    "visudo": "sudo",
    "yum": "yum",
    "zip": "zip",
}

DEBIAN_ONLY_PREFIXES = ("apparmor.", "network.firewall.ufw.")
RHEL_ONLY_PREFIXES = ("network.firewall.firewalld.", "selinux.")
DEBIAN_ONLY_EXACT = frozenset[str]()
RHEL_ONLY_EXACT = frozenset({"authselect.profile", "kernel.boot_param", "kernel.boot_param_absent", "pam.authselect"})


def plugin_os_mismatch(plugin_name: str, os_family: str | None, params: Dict[str, Any] | None = None) -> str | None:
    """Return a warning reason when a backend plugin does not match the target OS family."""
    params = params or {}
    if not os_family or os_family == "unknown":
        return None
    manager = str(params.get("manager", "auto"))
    if plugin_name.startswith("pkg."):
        if os_family == "debian" and manager in {"dnf", "yum", "zypper", "pacman"}:
            return f"{plugin_name} manager={manager} does not match DEBIAN-like target"
        if os_family == "rhel" and manager in {"apt", "apt-get", "zypper", "pacman"}:
            return f"{plugin_name} manager={manager} does not match RHEL-like target"
    if os_family == "debian" and (plugin_name in RHEL_ONLY_EXACT or plugin_name.startswith(RHEL_ONLY_PREFIXES)):
        return f"{plugin_name} is RHEL-like only; target is DEBIAN-like"
    if os_family == "rhel" and (plugin_name in DEBIAN_ONLY_EXACT or plugin_name.startswith(DEBIAN_ONLY_PREFIXES)):
        return f"{plugin_name} is DEBIAN-like only; target is RHEL-like"
    return None


def plugin_tools(plugin_name: str, params: Dict[str, Any] | None = None, os_family: str | None = None) -> tuple[str, ...]:
    """Return remote tools required by one plugin invocation for one OS family."""
    params = params or {}
    if plugin_os_mismatch(plugin_name, os_family, params):
        return ()
    tools: set[str] = set(EXACT_TOOL_REQUIREMENTS.get(plugin_name, ()))
    for prefix, prefix_tools in PREFIX_TOOL_REQUIREMENTS.items():
        if plugin_name.startswith(prefix):
            tools.update(prefix_tools)
    if os_family == "debian":
        tools.update(DEBIAN_TOOL_REQUIREMENTS.get(plugin_name, ()))
        for prefix, prefix_tools in DEBIAN_PREFIX_TOOL_REQUIREMENTS.items():
            if plugin_name.startswith(prefix):
                tools.update(prefix_tools)
    elif os_family == "rhel":
        tools.update(RHEL_TOOL_REQUIREMENTS.get(plugin_name, ()))
        for prefix, prefix_tools in RHEL_PREFIX_TOOL_REQUIREMENTS.items():
            if plugin_name.startswith(prefix):
                tools.update(prefix_tools)
    else:
        tools.update(DEBIAN_TOOL_REQUIREMENTS.get(plugin_name, ()))
        tools.update(RHEL_TOOL_REQUIREMENTS.get(plugin_name, ()))
        for prefix, prefix_tools in {**DEBIAN_PREFIX_TOOL_REQUIREMENTS, **RHEL_PREFIX_TOOL_REQUIREMENTS}.items():
            if plugin_name.startswith(prefix):
                tools.update(prefix_tools)
    for (name, param), param_tools in PARAM_TOOL_REQUIREMENTS.items():
        if plugin_name == name and params.get(param):
            tools.update(param_tools)
    manager = str(params.get("manager", "auto"))
    if plugin_name.startswith("pkg.") and os_family in {"debian", "rhel"}:
        if os_family == "debian" and manager in {"dnf", "yum"}:
            return ()
        if os_family == "rhel" and manager in {"apt", "apt-get"}:
            return ()
    return tuple(sorted(tools))


def package_for_tool(tool: str, os_family: str) -> str | None:
    """Return the package that should provide a tool on the requested OS family."""
    if os_family == "debian":
        return DEBIAN_PACKAGES.get(tool)
    if os_family == "rhel":
        return RHEL_PACKAGES.get(tool)
    return None


def collect_requirements(
    items: Iterable[Dict[str, Any]],
    os_by_target: Dict[str, TargetOS] | None = None,
) -> dict[str, Dict[str, Any]]:
    """Aggregate capability requirements by target from rendered plan items."""
    os_by_target = os_by_target or {}
    targets: dict[str, Dict[str, Any]] = {}
    for item in items:
        target = item["target"]
        os_info = os_by_target.get(target.name, TargetOS())
        entry = targets.setdefault(
            target.name,
            {
                "target": target.name,
                "host": target.host,
                "os": os_info,
                "tools": set(),
                "plugins": defaultdict(set),
                "skipped_plugins": [],
            },
        )
        plugin_name = str(item["plugin_name"])
        mismatch = plugin_os_mismatch(plugin_name, os_info.family, item.get("params", {}))
        if mismatch:
            entry["skipped_plugins"].append({"plugin": plugin_name, "reason": mismatch})
            continue
        tools = plugin_tools(plugin_name, item.get("params", {}), os_info.family)
        entry["tools"].update(tools)
        for tool in tools:
            entry["plugins"][tool].add(plugin_name)
    normalized: dict[str, Dict[str, Any]] = {}
    for name, entry in targets.items():
        os_info = entry["os"]
        tools = sorted(entry["tools"])
        normalized[name] = {
            "target": entry["target"],
            "host": entry["host"],
            "os": {
                "id": os_info.id,
                "id_like": list(os_info.id_like),
                "version_id": os_info.version_id,
                "family": os_info.family,
                "package_manager": os_info.package_manager,
            },
            "tools": tools,
            "packages": sorted({package for tool in tools if (package := package_for_tool(tool, os_info.family))}),
            "plugins": {tool: sorted(plugins) for tool, plugins in sorted(entry["plugins"].items())},
            "commands": [f"command -v {tool}" for tool in tools],
            "skipped_plugins": sorted(entry["skipped_plugins"], key=lambda item: item["plugin"]),
        }
    return normalized
