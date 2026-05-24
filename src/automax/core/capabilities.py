# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Job-scoped remote capability requirements."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable


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
    "iptables.chain": ("iptables",),
    "iptables.counter_assert": ("iptables",),
    "iptables.delete": ("iptables",),
    "iptables.exists_assert": ("iptables",),
    "iptables.list": ("iptables",),
    "iptables.policy": ("iptables",),
    "iptables.restore": ("iptables-restore",),
    "iptables.rule": ("iptables",),
    "iptables.save": ("iptables-save",),
    "kernel.boot_param": ("grubby",),
    "kernel.boot_param_absent": ("grubby",),
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
    "network.port_check": ("nc",),
    "nftables.apply": ("nft",),
    "nftables.export": ("nft",),
    "nftables.list": ("nft",),
    "nftables.rollback_file": ("nft",),
    "nftables.ruleset_assert": ("nft",),
    "nftables.validate": ("nft",),
    "pam.authselect": ("authselect",),
    "pam.validate": ("awk",),
    "pkg.clean": ("apt-get", "dnf", "yum", "zypper", "pacman"),
    "pkg.hold": ("apt-mark", "dnf", "yum", "zypper"),
    "pkg.owner": ("dpkg-query", "rpm", "pacman"),
    "pkg.pin": ("install",),
    "pkg.repo_priority": ("install",),
    "pkg.unhold": ("apt-mark", "dnf", "yum", "zypper"),
    "pkg.verify": ("dpkg", "rpm", "pacman"),
    "pkg.version_assert": ("dpkg-query", "rpm", "pacman"),
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
    "ufw.delete": ("ufw",),
    "ufw.disable": ("ufw",),
    "ufw.enable": ("ufw",),
    "ufw.reset": ("ufw",),
    "ufw.rule": ("ufw",),
    "ufw.status": ("ufw",),
}

PREFIX_TOOL_REQUIREMENTS: Dict[str, tuple[str, ...]] = {
    "archive.": ("tar", "unzip", "zip", "gzip"),
    "firewalld.": ("firewall-cmd",),
    "fs.attr": ("chattr",),
    "kernel.module.": ("modprobe", "lsmod"),
    "mount.": ("mount",),
    "process.": ("pgrep",),
    "systemctl.": ("systemctl",),
    "systemd.": ("systemctl",),
}

PARAM_TOOL_REQUIREMENTS: Dict[tuple[str, str], tuple[str, ...]] = {
    ("fs.write", "validate_command"): ("sh",),
    ("fs.template", "validate_command"): ("sh",),
    ("fs.line", "validate_command"): ("sh",),
    ("fs.replace", "validate_command"): ("sh",),
    ("archive.untar", "checksum"): ("sha256sum",),
    ("archive.unzip", "checksum"): ("sha256sum",),
}


def plugin_tools(plugin_name: str, params: Dict[str, Any] | None = None) -> tuple[str, ...]:
    """Return best-effort remote tools required by one plugin invocation."""
    params = params or {}
    tools: set[str] = set(EXACT_TOOL_REQUIREMENTS.get(plugin_name, ()))
    for prefix, prefix_tools in PREFIX_TOOL_REQUIREMENTS.items():
        if plugin_name.startswith(prefix):
            tools.update(prefix_tools)
    for (name, param), param_tools in PARAM_TOOL_REQUIREMENTS.items():
        if plugin_name == name and params.get(param):
            tools.update(param_tools)
    return tuple(sorted(tools))


def collect_requirements(items: Iterable[Dict[str, Any]]) -> dict[str, Dict[str, Any]]:
    """Aggregate capability requirements by target from rendered plan items."""
    targets: dict[str, Dict[str, Any]] = {}
    for item in items:
        target = item["target"]
        entry = targets.setdefault(
            target.name,
            {
                "target": target.name,
                "host": target.host,
                "tools": set(),
                "plugins": defaultdict(set),
            },
        )
        tools = plugin_tools(str(item["plugin_name"]), item.get("params", {}))
        entry["tools"].update(tools)
        for tool in tools:
            entry["plugins"][tool].add(str(item["plugin_name"]))
    normalized: dict[str, Dict[str, Any]] = {}
    for name, entry in targets.items():
        normalized[name] = {
            "target": entry["target"],
            "host": entry["host"],
            "tools": sorted(entry["tools"]),
            "plugins": {tool: sorted(plugins) for tool, plugins in sorted(entry["plugins"].items())},
            "commands": [f"command -v {tool}" for tool in sorted(entry["tools"])],
        }
    return normalized
