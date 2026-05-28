# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Builtin plugin operator-readiness audit helpers."""

from __future__ import annotations

from typing import Any

from automax.core.models import ExecutionContext, Target
from automax.plugins.registry import PluginRegistry


def _sample_value(name: str, schema: dict[str, Any]) -> Any:
    value = schema.get("default")
    expected = schema.get("types", schema.get("type", "string"))
    if isinstance(expected, str):
        expected_types = {expected}
    else:
        expected_types = {str(item) for item in expected}

    if value is not None and not isinstance(value, (list, dict)):
        if "boolean" in expected_types and isinstance(value, bool):
            return value
        if "integer" in expected_types and isinstance(value, int) and not isinstance(value, bool):
            return value
        if "number" in expected_types and isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        if ("string" in expected_types or "path" in expected_types) and isinstance(value, str):
            return value
    if "boolean" in expected_types:
        return True
    if "integer" in expected_types:
        if name in {"port", "smtp_port", "to_port"}:
            return 22
        if name in {"expected_status", "status"}:
            return 200
        if name == "max_percent":
            return 90
        if name == "vlan_id":
            return 100
        return 1
    if "number" in expected_types:
        return 1
    if "mapping" in expected_types:
        if isinstance(value, dict):
            return value
        return {"demo": "1"}
    if "list" in expected_types or "sequence" in expected_types:
        if isinstance(value, list):
            return value
        sample_lists = {
            "commands": ["/usr/bin/id"],
            "devices": ["/dev/sdb"],
            "entries": [{"domain": "*", "type": "soft", "item": "nofile", "value": 1024}],
            "interfaces": ["eth1"],
            "partitions": [{"number": 1, "start": "1MiB", "end": "100%"}],
            "paths": ["etc/hosts"],
            "patterns": ["*.bak"],
            "statements": ["SELECT 1"],
            "syscalls": ["openat"],
            "tools": ["sh"],
        }
        return sample_lists.get(name, ["demo"])
    if name == "url":
        return "https://example.invalid/health"
    if name in {"port", "smtp_port", "to_port"}:
        return 22
    if name == "mode":
        return "0644"
    if name == "rule":
        return "allow"
    if name == "state":
        return "present"
    if name == "backend":
        return "runtime"
    if name == "policy":
        return "ACCEPT"
    if name == "compression":
        return "gzip"
    if name == "checksum":
        return "sha256"
    if name == "rich_rule":
        return "rule family=ipv4 service name=ssh accept"
    if name == "source":
        return "10.0.0.0/8"
    if name == "archive":
        return "/tmp/app.tar.gz"
    if name == "value":
        return "1"
    if name == "query":
        return "SELECT 1 AS value"
    if name == "acl":
        return "u:app:rwx"
    if name == "attrs":
        return "i"
    if name == "schedule":
        return "* * * * *"
    if name == "command":
        return "echo automax"
    if name == "content":
        return "managed by automax\n"
    return "demo"


def sample_params(plugin: Any) -> dict[str, Any]:
    """Build conservative parameters for plugin audit renderers."""
    params = {
        name: _sample_value(name, plugin.parameter_schema.get(name, {}))
        for name in plugin.required_params
    }
    skipped_optional = {
        "attachments",
        "bcc",
        "cc",
        "checks",
        "connection",
        "env",
        "excludes",
        "features",
        "files",
        "groups",
        "headers",
        "options",
        "packages",
        "rules",
        "search",
        "ssh_options",
        "values",
    }
    for name in plugin.optional_params:
        if name in skipped_optional:
            continue
        params.setdefault(name, _sample_value(name, plugin.parameter_schema.get(name, {})))

    if plugin.name.startswith("db."):
        params.setdefault("connection", {"path": "/tmp/automax.sqlite"})
    if plugin.name == "db.health":
        params["engine"] = "sqlite"
        params["connection"] = {"path": "/tmp/automax.sqlite"}
    if plugin.name in {"backup.prune", "backup.restore", "backup.rotate", "network.firewall.iptables.restore", "lvm.lv_remove", "lvm.pv_remove", "lvm.vg_remove"}:
        params["confirm"] = True
    if plugin.name == "plugin.requirements":
        params["plugin"] = "transfer.rsync"
    if plugin.name == "backup.directory":
        params["compression"] = "none"
    if plugin.name == "backup.verify":
        params["checksum"] = "sha256"
    if plugin.name == "archive.compress":
        params["dest"] = "/tmp/automax-demo.gz"
    if plugin.name == "archive.decompress":
        params["archive"] = "/tmp/automax-demo.gz"
    if plugin.name == "block.wipe_signatures":
        params["force"] = True
    if plugin.name == "fs.template":
        params["src"] = "README.md"
    if plugin.name == "network.link.interface":
        params["backend"] = "runtime"
    if plugin.name in {"process.kill", "process.signal", "process.wait"}:
        params.pop("pid", None)
        params["pattern"] = "automax-demo"
    if plugin.name == "mail.send":
        params["from"] = "automax@example.invalid"
        params["to"] = ["ops@example.invalid"]
    if plugin.name == "network.firewall.nftables.apply" or plugin.name == "network.firewall.nftables.validate":
        params["content"] = "flush ruleset\n"
    if plugin.name == "pki.ca_install":
        params["name"] = "automax-demo"
        params["content"] = "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n"
    if plugin.name == "selinux.mode":
        params["state"] = "enforcing"
    if plugin.name == "fs.quota":
        params["type"] = "user"
    if plugin.name == "apparmor.profile_assert":
        params["state"] = "enforce"
    if plugin.name == "auditd.backlog_assert":
        params["max_lost"] = 0
        params["max_backlog"] = 8192
    if plugin.name == "chrony.tracking_assert":
        params["max_offset"] = 1.0
        params["max_stratum"] = 16
    if plugin.name == "network.firewall.iptables.counter_assert":
        params["min_packets"] = 1
    if plugin.name == "fs.replace":
        params["count"] = 0
        params["match_count_assert"] = 1
    if plugin.name == "sshd.config":
        params["match_blocks"] = [{"match": "User deploy", "settings": {"X11Forwarding": "no"}}]
    if plugin.name == "network.dns":
        params["backend"] = "plain-file"
    if plugin.name in {"network.route.add", "network.route.remove"}:
        params["backend"] = "runtime"
        params["persist"] = False
    if plugin.name == "network.route.facts":
        params["family"] = "inet"
    if plugin.name in {"network.link.interface", "network.link.bond", "network.link.vlan"}:
        params["state"] = "up"
    return params


def audit_plugin_registry(registry: PluginRegistry) -> dict[str, Any]:
    """Audit registered plugins for operator preview/readiness coverage."""
    context = ExecutionContext(
        run_id="plugin-audit",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node", host="host"),
        vars={},
        outputs={},
        secrets={},
    )
    failures: list[str] = []
    checked = 0
    for name in registry.names():
        checked += 1
        plugin = registry.get(name)
        params = sample_params(plugin)
        try:
            commands = plugin.manual_commands(params, context)
            if not commands or not all(isinstance(command, str) and command.strip() for command in commands):
                failures.append(f"{name}: empty manual_commands")
            rendered = "\n".join(commands)
            if "mktemp" in rendered and "trap 'rm -f" not in rendered:
                failures.append(f"{name}: mktemp manual_commands without cleanup trap")
        except Exception as exc:  # pragma: no cover - surfaced to operator output
            failures.append(f"{name}: manual_commands raised {exc!r}")
        try:
            preview = plugin.diff_preview(params, context)
            reason = plugin.diff_preview_reason(params, context)
            if not preview and not reason:
                failures.append(f"{name}: no diff_preview and no diff_preview_reason")
        except Exception as exc:  # pragma: no cover - surfaced to operator output
            failures.append(f"{name}: diff_preview raised {exc!r}")
        try:
            dry_run = plugin.dry_run(params, context)
            if not dry_run.ok or dry_run.changed:
                failures.append(f"{name}: dry_run not safe/unchanged")
        except Exception as exc:  # pragma: no cover - surfaced to operator output
            failures.append(f"{name}: dry_run raised {exc!r}")

    return {
        "ok": not failures,
        "checked": checked,
        "failures": failures,
        "failure_count": len(failures),
    }
