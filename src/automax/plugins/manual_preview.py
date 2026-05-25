# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Fallback manual-command and operation-preview renderers for legacy plugins."""

from __future__ import annotations

import json
from difflib import unified_diff
from shlex import quote as shell_quote
from typing import Any, Dict

from automax.core.models import ExecutionContext


def _q(value: Any) -> str:
    return shell_quote(str(value))


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return [str(value)]


def _packages(params: Dict[str, Any]) -> str:
    packages = _list(params.get("packages") or params.get("name") or "automax-demo")
    return " ".join(_q(item) for item in packages)


def _package_manager_command(params: Dict[str, Any], apt: str, dnf: str, yum: str, zypper: str) -> str:
    sudo = _sudo(params)
    return (
        "if command -v apt-get >/dev/null 2>&1; then "
        f"{sudo}{apt}; "
        "elif command -v dnf >/dev/null 2>&1; then "
        f"{sudo}{dnf}; "
        "elif command -v yum >/dev/null 2>&1; then "
        f"{sudo}{yum}; "
        "elif command -v zypper >/dev/null 2>&1; then "
        f"{sudo}{zypper}; "
        "else echo 'no supported package manager found' >&2; exit 1; fi"
    )


def _systemctl(params: Dict[str, Any], action: str) -> str:
    service = params.get("service", "demo.service")
    sudo = _sudo(params)
    scope = " --user" if bool(params.get("user", False)) else ""
    return f"{sudo}systemctl{scope} {action} {_q(service)}"


def _firewalld(params: Dict[str, Any], action: str) -> str:
    sudo = _sudo(params)
    zone = f" --zone={_q(params['zone'])}" if params.get("zone") else ""
    permanent = " --permanent" if bool(params.get("permanent", True)) else ""
    reload_cmd = f" && {sudo}firewall-cmd --reload" if bool(params.get("reload", False)) else ""
    return f"{sudo}firewall-cmd{zone}{permanent} {action}{reload_cmd}"


def _ssh_opts(params: Dict[str, Any]) -> str:
    if params.get("port"):
        return f" -p {_q(params['port'])}"
    return ""


def _db_connection(params: Dict[str, Any]) -> Dict[str, Any]:
    connection = params.get("connection")
    if isinstance(connection, dict):
        return connection
    return {}


def _db_query(params: Dict[str, Any]) -> str:
    query = params.get("query") or "SELECT 1"
    return str(query).replace("'", "'\\''")


def fallback_manual_commands(plugin_name: str, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    """Return deterministic manual commands for legacy plugins that do not override them."""
    sudo = _sudo(params)
    path = str(params.get("path", "/tmp/automax-demo"))
    name = str(params.get("name", "demo"))

    if plugin_name.startswith("systemctl."):
        action = plugin_name.split(".", 1)[1]
        return [_systemctl(params, "daemon-reload" if action == "daemon_reload" else action.replace("_", "-"))]

    if plugin_name == "apparmor.profile":
        profile = params.get("profile", path)
        state = params.get("state", "present")
        return [f"{sudo}apparmor_parser {'-R' if state == 'absent' else '-r'} {_q(profile)}"]
    if plugin_name == "apparmor.reload":
        return [f"{sudo}systemctl reload apparmor || {sudo}service apparmor reload"]
    if plugin_name == "apparmor.status":
        return [f"{sudo}aa-status"]

    if plugin_name.startswith("assert."):
        if plugin_name == "assert.command":
            return [str(params.get("command", "true"))]
        if plugin_name in {"assert.file", "assert.path"}:
            return [f"test -e {_q(path)}"]
        if plugin_name == "assert.disk":
            return [f"df -Pm {_q(path)}"]
        if plugin_name == "assert.tcp":
            return [f"nc -z -w {_q(params.get('connect_timeout', 5))} {_q(params.get('host', '127.0.0.1'))} {_q(params.get('port', 22))}"]

    if plugin_name.startswith("db.") and plugin_name.endswith(".query"):
        conn = _db_connection(params)
        if plugin_name == "db.sqlite.query":
            database = conn.get("path") or conn.get("database") or params.get("path") or params.get("database") or "database.sqlite"
            return [f"sqlite3 {_q(database)} '{_db_query(params)};'"]
        if plugin_name == "db.postgres.query":
            return [f"PGPASSWORD=*** psql -h {_q(conn.get('host', 'localhost'))} -U {_q(conn.get('user', 'postgres'))} -d {_q(conn.get('database', 'postgres'))} -c '{_db_query(params)};'"]
        if plugin_name == "db.mysql.query":
            return [f"MYSQL_PWD=*** mysql -h {_q(conn.get('host', 'localhost'))} -u {_q(conn.get('user', 'root'))} {_q(conn.get('database', 'mysql'))} -e '{_db_query(params)};'"]
        if plugin_name == "db.oracle.query":
            return [f"echo '{_db_query(params)};' | sqlplus -s {_q(conn.get('user', 'user'))}/***@{_q(conn.get('dsn', 'db'))}"]

    if plugin_name.startswith("facts."):
        if plugin_name == "facts.os":
            return ["cat /etc/os-release 2>/dev/null || uname -a"]
        if plugin_name == "facts.network":
            return ["ip -brief addr && ip route"]
        if plugin_name == "facts.packages":
            return [_package_manager_command(params, "dpkg-query -W", "rpm -qa", "rpm -qa", "rpm -qa")]
        if plugin_name == "facts.services":
            return ["systemctl list-units --type=service --no-pager || service --status-all"]
        return ["uname -a && cat /etc/os-release 2>/dev/null || true"]

    if plugin_name.startswith("firewalld."):
        if plugin_name == "firewalld.port":
            port = f"{params.get('port', 22)}/{params.get('protocol', 'tcp')}"
            verb = "--remove-port" if params.get("state") == "absent" else "--add-port"
            return [_firewalld(params, f"{verb}={_q(port)}")]
        if plugin_name == "firewalld.service":
            verb = "--remove-service" if params.get("state") == "absent" else "--add-service"
            return [_firewalld(params, f"{verb}={_q(params.get('service', 'ssh'))}")]
        if plugin_name == "firewalld.rich_rule":
            verb = "--remove-rich-rule" if params.get("state") == "absent" else "--add-rich-rule"
            return [_firewalld(params, f"{verb}={_q(params.get('rich_rule', 'rule family=ipv4 service name=ssh accept'))}")]
        if plugin_name == "firewalld.reload":
            return [f"{sudo}firewall-cmd --reload"]

    if plugin_name.startswith("ufw."):
        if plugin_name == "ufw.enable":
            return [f"{sudo}ufw --force enable"]
        if plugin_name == "ufw.disable":
            return [f"{sudo}ufw disable"]
        if plugin_name == "ufw.status":
            return [f"{sudo}ufw status verbose"]
        if plugin_name == "ufw.rule":
            state = str(params.get("state", "allow"))
            rule = str(params.get("rule", state))
            return [f"{sudo}ufw {rule}"]

    if plugin_name.startswith("nftables."):
        if plugin_name == "nftables.validate":
            src = params.get("src")
            return [f"{sudo}nft -c -f {_q(src)}" if src else f"cat <<'EOF' | {sudo}nft -c -f -\n{params.get('content', '')}\nEOF"]
        if plugin_name == "nftables.apply":
            src = params.get("src")
            return [f"{sudo}nft -f {_q(src)}" if src else f"cat <<'EOF' | {sudo}nft -f -\n{params.get('content', '')}\nEOF"]

    if plugin_name.startswith("pkg."):
        packages = _packages(params)
        if plugin_name == "pkg.install":
            return [_package_manager_command(params, f"apt-get update && apt-get install -y {packages}", f"dnf install -y {packages}", f"yum install -y {packages}", f"zypper --non-interactive install {packages}")]
        if plugin_name == "pkg.remove":
            return [_package_manager_command(params, f"apt-get remove -y {packages}", f"dnf remove -y {packages}", f"yum remove -y {packages}", f"zypper --non-interactive remove {packages}")]
        if plugin_name == "pkg.upgrade":
            return [_package_manager_command(params, "apt-get upgrade -y", "dnf upgrade -y", "yum update -y", "zypper --non-interactive update")]
        if plugin_name == "pkg.update_cache":
            return [_package_manager_command(params, "apt-get update", "dnf makecache", "yum makecache", "zypper --non-interactive refresh")]
        if plugin_name == "pkg.query":
            return [_package_manager_command(params, f"dpkg-query -W {packages}", f"rpm -q {packages}", f"rpm -q {packages}", f"rpm -q {packages}")]
        if plugin_name == "pkg.key.remove":
            return [f"{sudo}rm -f {_q(params.get('dest', f'/etc/apt/keyrings/{name}.gpg'))}"]
        if plugin_name in {"pkg.key.add", "pkg.repo.add", "pkg.repo.remove"}:
            return [f"# render package repository/key change for {plugin_name}; inspect generated job preview before manual execution"]

    if plugin_name.startswith("user."):
        if plugin_name == "user.create":
            return [f"id -u {_q(name)} >/dev/null 2>&1 || {sudo}useradd {_q(name)}"]
        if plugin_name == "user.remove":
            return [f"{sudo}userdel {'-r ' if params.get('remove_home') else ''}{_q(name)}"]
        if plugin_name == "user.exists":
            return [f"id {_q(name)}"]
        if plugin_name == "user.lock":
            return [f"{sudo}usermod -L {_q(name)}"]
        if plugin_name == "user.unlock":
            return [f"{sudo}usermod -U {_q(name)}"]
        if plugin_name == "user.set_password":
            return [f"echo '{name}:***' | {sudo}chpasswd"]
        if plugin_name == "user.modify":
            return [f"{sudo}usermod {_q(name)}"]

    if plugin_name.startswith("group."):
        if plugin_name == "group.create":
            return [f"getent group {_q(name)} >/dev/null || {sudo}groupadd {_q(name)}"]
        if plugin_name == "group.remove":
            return [f"{sudo}groupdel {_q(name)}"]
        if plugin_name == "group.exists":
            return [f"getent group {_q(name)}"]

    if plugin_name.startswith("fs."):
        if plugin_name == "fs.cd":
            return [f"cd {_q(path)}"]
        if plugin_name == "fs.copy":
            return [f"cp {'-a ' if params.get('preserve') else ''}{'-r ' if params.get('recursive') else ''}{_q(params.get('src', '/tmp/source'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.exists":
            return [f"test -e {_q(path)}"]
        if plugin_name == "fs.find":
            return [f"find {_q(path)}"]
        if plugin_name == "fs.line":
            return [f"grep -Fqx {_q(params.get('line', 'line'))} {_q(path)} || printf '%s\\n' {_q(params.get('line', 'line'))} >> {_q(path)}"]
        if plugin_name == "fs.move":
            return [f"mv {_q(params.get('src', '/tmp/source'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.read":
            return [f"cat {_q(path)}"]
        if plugin_name == "fs.stat":
            return [f"stat {_q(path)}"]
        if plugin_name == "fs.symlink.create":
            return [f"ln -sfn {_q(params.get('src', '/tmp/source'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.symlink.remove":
            return [f"test -L {_q(path)} && rm -f {_q(path)} || true"]
        if plugin_name == "fs.template":
            return [f"install -D {_q(params.get('src', '/tmp/template'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.write":
            return [f"cat > {_q(path)} <<'EOF'\n{params.get('content', '')}\nEOF"]

    if plugin_name in {"fstab.entry", "mount.present"}:
        return [f"{sudo}mount {_q(params.get('path', path))}"]
    if plugin_name == "mount.absent":
        return [f"{sudo}umount {_q(path)}"]

    if plugin_name.startswith("process."):
        pattern = params.get("pattern")
        if plugin_name == "process.kill":
            if params.get("pid"):
                return [f"{sudo}kill -{_q(params.get('signal', 'TERM'))} {_q(params['pid'])}"]
            return [f"{sudo}pkill -{_q(params.get('signal', 'TERM'))} -f {_q(pattern or 'process')}"]
        if plugin_name == "process.wait":
            return [f"timeout {_q(params.get('timeout', 60))} sh -c 'until pgrep -f {_q(pattern or 'process')} >/dev/null; do sleep {_q(params.get('interval', 2))}; done'"]

    if plugin_name.startswith("selinux."):
        if plugin_name == "selinux.boolean":
            return [f"{sudo}setsebool {'-P ' if params.get('persist', True) else ''}{_q(params.get('name', 'httpd_can_network_connect'))} {_q('on' if params.get('value', True) else 'off')}"]
        if plugin_name == "selinux.mode":
            return [f"{sudo}setenforce {_q(params.get('state', 'enforcing'))}"]
        if plugin_name in {"selinux.context", "selinux.fcontext"}:
            return [f"{sudo}semanage fcontext -a -t {_q(params.get('selinux_type', 'var_t'))} {_q(path)}"]
        if plugin_name == "selinux.restorecon":
            return [f"{sudo}restorecon {'-R ' if params.get('recursive') else ''}{_q(path)}"]

    if plugin_name == "ssh.authorized_key":
        return [f"{sudo}install -d -m 0700 ~{_q(params.get('user', name))}/.ssh && echo {_q(params.get('key', 'ssh-ed25519 AAAA demo'))} >> ~{_q(params.get('user', name))}/.ssh/authorized_keys"]
    if plugin_name == "sudoers.dropin":
        return [f"{sudo}visudo -cf {_q(params.get('path', '/etc/sudoers'))}"]

    if plugin_name.startswith("transfer."):
        src = params.get("src", "/tmp/source")
        dest = params.get("dest", "/tmp/dest")
        if plugin_name == "transfer.download":
            return [f"scp{_ssh_opts(params)} {_q(str(src))} {_q(str(dest))}"]
        if plugin_name == "transfer.upload":
            return [f"scp{_ssh_opts(params)} {_q(str(src))} {_q(str(dest))}"]
        if plugin_name == "transfer.sync":
            return [f"rsync -a {_q(str(src))}/ {_q(str(dest))}/"]

    if plugin_name.startswith("wait."):
        timeout = params.get("timeout", 60)
        interval = params.get("interval", 2)
        if plugin_name == "wait.command":
            return [f"timeout {_q(timeout)} sh -c 'until {params.get('command', 'true')}; do sleep {_q(interval)}; done'"]
        if plugin_name in {"wait.file", "wait.path"}:
            return [f"timeout {_q(timeout)} sh -c 'until test -e {_q(path)}; do sleep {_q(interval)}; done'"]
        if plugin_name == "wait.process":
            return [f"timeout {_q(timeout)} sh -c 'until pgrep -f {_q(params.get('pattern', 'process'))} >/dev/null; do sleep {_q(interval)}; done'"]
        if plugin_name == "wait.tcp":
            return [f"timeout {_q(timeout)} sh -c 'until nc -z -w {_q(params.get('connect_timeout', 5))} {_q(params.get('host', '127.0.0.1'))} {_q(params.get('port', 22))}; do sleep {_q(interval)}; done'"]

    if plugin_name in {"cron.entry", "cron.file"}:
        return [f"{sudo}crontab -l 2>/dev/null | sed '/# automax:{_q(name)}/d' | {sudo}crontab -"]

    return [
        f"printf '%s\\n' {_q('No direct shell renderer for controller-side plugin ' + plugin_name + '; rerun the Automax substep with preview output as the source of truth.')}"
    ]


def fallback_diff_preview(plugin_name: str, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
    """Return an operation-plan preview for plugins without file-level diffs."""
    commands = fallback_manual_commands(plugin_name, params, context)
    desired = "".join(f"$ {command}\n" for command in commands)
    diff = "".join(
        unified_diff(
            [],
            desired.splitlines(keepends=True),
            fromfile=f"{plugin_name} (current plan)",
            tofile=f"{plugin_name} (manual plan)",
        )
    )
    return [{"path": f"plugin:{plugin_name}", "kind": "operation-plan", "diff": diff}]


def fallback_dry_run_data(plugin_name: str, params: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
    commands = fallback_manual_commands(plugin_name, params, context)
    preview = fallback_diff_preview(plugin_name, params, context)
    return {"params": params, "manual_commands": commands, "diff_preview": preview}


def serialize_params(params: Dict[str, Any]) -> str:
    return json.dumps(params, sort_keys=True, default=str)
