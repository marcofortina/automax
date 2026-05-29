# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Fallback manual-command and operation-preview renderers for legacy plugins."""

from __future__ import annotations

import json
from difflib import unified_diff
from shlex import quote as shell_quote
from typing import Any, Dict

from automax.core.models import ExecutionContext
from automax.plugins.remote_utils import heredoc_to_file, heredoc_to_stdin, sudo_prefix


def _q(value: Any) -> str:
    return shell_quote(str(value))



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
    sudo = sudo_prefix(params, default=True)
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
    sudo = sudo_prefix(params, default=True)
    scope = " --user" if bool(params.get("user", False)) else ""
    return f"{sudo}systemctl{scope} {action} {_q(service)}"


def _firewalld(params: Dict[str, Any], action: str) -> str:
    sudo = sudo_prefix(params, default=True)
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


def _groupadd_flags(params: Dict[str, Any]) -> str:
    flags: list[str] = []
    if bool(params.get("system", False)):
        flags.append("--system")
    if params.get("gid") is not None:
        flags.extend(["--gid", _q(params["gid"])])
    return " ".join(flags)


def _useradd_flags(params: Dict[str, Any]) -> str:
    flags: list[str] = []
    if bool(params.get("system", False)):
        flags.append("--system")
    if params.get("uid") is not None:
        flags.extend(["--uid", _q(params["uid"])])
    if params.get("group"):
        flags.extend(["--gid", _q(params["group"])])
    groups = _list(params.get("groups"))
    if groups:
        flags.extend(["--groups", _q(",".join(groups))])
    if params.get("shell"):
        flags.extend(["--shell", _q(params["shell"])])
    if params.get("home"):
        flags.extend(["--home-dir", _q(params["home"])])
    if "create_home" in params:
        flags.append("--create-home" if bool(params.get("create_home")) else "--no-create-home")
    if params.get("comment"):
        flags.extend(["--comment", _q(params["comment"])])
    return " ".join(flags)


def fallback_manual_commands(plugin_name: str, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    """Return deterministic manual commands for legacy plugins that do not override them."""
    sudo = sudo_prefix(params, default=True)
    path = str(params.get("path", "/tmp/automax-demo"))
    name = str(params.get("name", "demo"))

    if plugin_name == "system.systemd.daemon_reload":
        return [_systemctl(params, "daemon-reload")]
    if plugin_name.startswith("system.service."):
        action = plugin_name.rsplit(".", 1)[1]
        action_map = {"active_check": "is-active", "enabled_check": "is-enabled"}
        return [_systemctl(params, action_map.get(action, action.replace("_", "-")))]

    if plugin_name == "security.apparmor.profile":
        profile = params.get("profile", path)
        state = params.get("state", "present")
        return [f"{sudo}apparmor_parser {'-R' if state == 'absent' else '-r'} {_q(profile)}"]
    if plugin_name == "security.apparmor.reload":
        return [f"{sudo}systemctl reload apparmor || {sudo}service apparmor reload"]
    if plugin_name == "security.apparmor.status":
        return [f"{sudo}aa-status"]

    if plugin_name.startswith("assert."):
        if plugin_name == "storage.usage.disk.check":
            return [f"df -Pm {_q(path)}"]

    if plugin_name == "network.connectivity.port.check":
        return [f"nc -z -w {_q(params.get('timeout', params.get('connect_timeout', 5)))} {_q(params.get('host', '127.0.0.1'))} {_q(params.get('port', 22))}"]
    if plugin_name == "network.connectivity.port.wait":
        return [f"i=0; until nc -z -w {_q(params.get('timeout', 5))} {_q(params.get('host', '127.0.0.1'))} {_q(params.get('port', 22))}; do i=$((i + 1)); [ $i -ge {_q(params.get('retries', 30))} ] && exit 1; sleep {_q(params.get('interval', 2))}; done"]

    if plugin_name.startswith("database.") and plugin_name.endswith(".query"):
        conn = _db_connection(params)
        if plugin_name == "database.sqlite.query":
            database = conn.get("path") or conn.get("database") or params.get("path") or params.get("database") or "database.sqlite"
            return [f"sqlite3 {_q(database)} '{_db_query(params)};'"]
        if plugin_name == "database.postgres.query":
            return [f"PGPASSWORD=*** psql -h {_q(conn.get('host', 'localhost'))} -U {_q(conn.get('user', 'postgres'))} -d {_q(conn.get('database', 'postgres'))} -c '{_db_query(params)};'"]
        if plugin_name == "database.mysql.query":
            return [f"MYSQL_PWD=*** mysql -h {_q(conn.get('host', 'localhost'))} -u {_q(conn.get('user', 'root'))} {_q(conn.get('database', 'mysql'))} -e '{_db_query(params)};'"]
        if plugin_name == "database.oracle.query":
            return [f"echo '{_db_query(params)};' | sqlplus -s {_q(conn.get('user', 'user'))}/***@{_q(conn.get('dsn', 'db'))}"]

    if plugin_name in {"os.facts", "os.package.facts", "network.link.facts", "system.service.facts"}:
        if plugin_name == "os.facts":
            return ["cat /etc/os-release 2>/dev/null || uname -a"]
        if plugin_name == "network.link.facts":
            return ["ip -brief addr && ip route"]
        if plugin_name == "os.package.facts":
            return [_package_manager_command(params, "dpkg-query -W", "rpm -qa", "rpm -qa", "rpm -qa")]
        if plugin_name == "system.service.facts":
            return ["systemctl list-units --type=service --no-pager || service --status-all"]
        return ["uname -a && cat /etc/os-release 2>/dev/null || true"]

    if plugin_name.startswith("firewalld."):
        if plugin_name == "network.firewall.firewalld.port":
            port = f"{params.get('port', 22)}/{params.get('protocol', 'tcp')}"
            verb = "--remove-port" if params.get("state") == "absent" else "--add-port"
            return [_firewalld(params, f"{verb}={_q(port)}")]
        if plugin_name == "network.firewall.firewalld.service":
            verb = "--remove-service" if params.get("state") == "absent" else "--add-service"
            return [_firewalld(params, f"{verb}={_q(params.get('service', 'ssh'))}")]
        if plugin_name == "network.firewall.firewalld.rich_rule":
            verb = "--remove-rich-rule" if params.get("state") == "absent" else "--add-rich-rule"
            return [_firewalld(params, f"{verb}={_q(params.get('rich_rule', 'rule family=ipv4 service name=ssh accept'))}")]
        if plugin_name == "network.firewall.firewalld.reload":
            return [f"{sudo}firewall-cmd --reload"]

    if plugin_name.startswith("ufw."):
        if plugin_name == "network.firewall.ufw.enable":
            return [f"{sudo}ufw --force enable"]
        if plugin_name == "network.firewall.ufw.disable":
            return [f"{sudo}ufw disable"]
        if plugin_name == "network.firewall.ufw.status":
            return [f"{sudo}ufw status verbose"]
        if plugin_name == "network.firewall.ufw.rule":
            state = str(params.get("state", "allow"))
            rule = str(params.get("rule", state))
            return [f"{sudo}ufw {rule}"]

    if plugin_name.startswith("nftables."):
        if plugin_name == "network.firewall.nftables.validate":
            src = params.get("src")
            return [f"{sudo}nft -c -f {_q(src)}" if src else heredoc_to_stdin(f"{sudo}nft -c -f -", params.get("content", ""))]
        if plugin_name == "network.firewall.nftables.apply":
            src = params.get("src")
            return [f"{sudo}nft -f {_q(src)}" if src else heredoc_to_stdin(f"{sudo}nft -f -", params.get("content", ""))]

    if plugin_name.startswith("os.package."):
        packages = _packages(params)
        if plugin_name == "os.package.install":
            return [_package_manager_command(params, f"apt-get update && apt-get install -y {packages}", f"dnf install -y {packages}", f"yum install -y {packages}", f"zypper --non-interactive install {packages}")]
        if plugin_name == "os.package.remove":
            return [_package_manager_command(params, f"apt-get remove -y {packages}", f"dnf remove -y {packages}", f"yum remove -y {packages}", f"zypper --non-interactive remove {packages}")]
        if plugin_name == "os.package.upgrade":
            return [_package_manager_command(params, "apt-get upgrade -y", "dnf upgrade -y", "yum update -y", "zypper --non-interactive update")]
        if plugin_name == "os.package.update_cache":
            return [_package_manager_command(params, "apt-get update", "dnf makecache", "yum makecache", "zypper --non-interactive refresh")]
        if plugin_name == "os.package.query":
            return [_package_manager_command(params, f"dpkg-query -W {packages}", f"rpm -q {packages}", f"rpm -q {packages}", f"rpm -q {packages}")]
        if plugin_name == "os.package.key.remove":
            return [f"{sudo}rm -f {_q(params.get('dest', f'/etc/apt/keyrings/{name}.gpg'))}"]
        if plugin_name in {"os.package.key.check", "os.package.repo.check"}:
            return [f"test -e {_q(params.get('dest', name))}"]
        if plugin_name in {"os.package.key.add", "os.package.repo.add", "os.package.repo.remove", "os.package.repo.priority.set", "os.package.repo.priority.check"}:
            return [f"# render package repository/key change for {plugin_name}; inspect generated job preview before manual execution"]

    if plugin_name.startswith("identity.user."):
        if plugin_name == "identity.user.create":
            flags = _useradd_flags(params)
            flag_text = f" {flags}" if flags else ""
            return [f"id -u {_q(name)} >/dev/null 2>&1 || {sudo}useradd{flag_text} {_q(name)}"]
        if plugin_name == "identity.user.remove":
            return [f"{sudo}userdel {'-r ' if params.get('remove_home') else ''}{_q(name)}"]
        if plugin_name == "identity.user.check":
            return [f"id {_q(name)}"]
        if plugin_name == "identity.user.lock":
            return [f"{sudo}usermod -L {_q(name)}"]
        if plugin_name == "identity.user.unlock":
            return [f"{sudo}usermod -U {_q(name)}"]
        if plugin_name == "identity.user.password.set":
            return [f"echo '{name}:***' | {sudo}chpasswd"]
        if plugin_name == "identity.user.modify":
            return [f"{sudo}usermod {_q(name)}"]

    if plugin_name.startswith("identity.group."):
        if plugin_name == "identity.group.create":
            flags = _groupadd_flags(params)
            flag_text = f" {flags}" if flags else ""
            return [f"getent group {_q(name)} >/dev/null || {sudo}groupadd{flag_text} {_q(name)}"]
        if plugin_name == "identity.group.remove":
            return [f"{sudo}groupdel {_q(name)}"]
        if plugin_name == "identity.group.check":
            return [f"getent group {_q(name)}"]

    if plugin_name.startswith("fs."):
        if plugin_name == "fs.path.copy":
            return [f"cp {'-a ' if params.get('preserve') else ''}{'-r ' if params.get('recursive') else ''}{_q(params.get('src', '/tmp/source'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.dir.create":
            return [f"test -d {_q(path)} && ! test -L {_q(path)} || mkdir -p -- {_q(path)}"]
        if plugin_name == "fs.dir.remove":
            return [f"test ! -e {_q(path)} || rmdir -- {_q(path)}"]
        if plugin_name == "fs.dir.check":
            return [f"test -d {_q(path)} && ! test -L {_q(path)}"]
        if plugin_name == "fs.dir.wait":
            return [f"for i in $(seq 1 {_q(params.get('retries', 12))}); do test -d {_q(path)} && ! test -L {_q(path)} && exit 0; sleep {_q(params.get('interval', 5))}; done; exit 1"]
        if plugin_name == "fs.file.create":
            return [f"test -f {_q(path)} && ! test -L {_q(path)} || touch -- {_q(path)}"]
        if plugin_name == "fs.file.remove":
            return [f"test ! -e {_q(path)} || rm -f -- {_q(path)}"]
        if plugin_name == "fs.file.check":
            return [f"test -f {_q(path)} && ! test -L {_q(path)}"]
        if plugin_name == "fs.file.wait":
            return [f"for i in $(seq 1 {_q(params.get('retries', 12))}); do test -f {_q(path)} && ! test -L {_q(path)} && exit 0; sleep {_q(params.get('interval', 5))}; done; exit 1"]
        if plugin_name == "fs.symlink.check":
            return [f"test -L {_q(path)}"]
        if plugin_name == "fs.symlink.wait":
            return [f"for i in $(seq 1 {_q(params.get('retries', 12))}); do test -L {_q(path)} && exit 0; sleep {_q(params.get('interval', 5))}; done; exit 1"]
        if plugin_name == "fs.path.find":
            return [f"find {_q(path)}"]
        if plugin_name == "fs.file.line":
            return [f"grep -Fqx {_q(params.get('line', 'line'))} {_q(path)} || printf '%s\\n' {_q(params.get('line', 'line'))} >> {_q(path)}"]
        if plugin_name == "fs.path.move":
            return [f"mv {_q(params.get('src', '/tmp/source'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.file.read":
            prefix = "sudo " if params.get("sudo") else ""
            return [f"{prefix}cat {_q(path)}"]
        if plugin_name == "fs.permission.mode.get":
            return [f"stat -c %a {_q(path)}"]
        if plugin_name == "fs.permission.mode.check":
            return [f'test -e {_q(path)} && test "$(stat -c %a {_q(path)})" = {_q(params.get("mode", "0644"))} || true']
        if plugin_name == "fs.permission.mode.set":
            return [f"chmod {_q(params.get('mode', '0644'))} {_q(path)}"]
        if plugin_name == "fs.permission.owner.get":
            return [f"stat -c '%U|%G' {_q(path)}"]
        if plugin_name == "fs.permission.owner.check":
            return [f"test -e {_q(path)} && stat -c '%U|%G' {_q(path)} || true"]
        if plugin_name == "fs.permission.owner.set":
            owner_group = f"{params.get('owner', '')}:{params.get('group', '')}"
            return [f"chown {_q(owner_group)} {_q(path)}"]
        if plugin_name == "fs.path.stat":
            return [f"stat {_q(path)}"]
        if plugin_name == "fs.symlink.create":
            return [f"ln -sfn {_q(params.get('src', '/tmp/source'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.symlink.remove":
            return [f"test -L {_q(path)} && rm -f {_q(path)} || true"]
        if plugin_name == "fs.file.template":
            return [f"install -D {_q(params.get('src', '/tmp/template'))} {_q(params.get('dest', '/tmp/dest'))}"]
        if plugin_name == "fs.file.write":
            return [heredoc_to_file(path, params.get("content", ""))]

    if plugin_name in {"storage.fstab.add", "storage.mount.add"}:
        return [f"{sudo}mount {_q(params.get('path', path))}"]
    if plugin_name == "storage.mount.remove":
        return [f"{sudo}umount {_q(path)}"]

    if plugin_name.startswith("system.process."):
        pattern = params.get("pattern")
        if plugin_name in {"system.process.kill", "system.process.signal"}:
            if params.get("pid"):
                return [f"{sudo}kill -{_q(params.get('signal', 'TERM'))} {_q(params['pid'])}"]
            return [f"{sudo}pkill -{_q(params.get('signal', 'TERM'))} -f {_q(pattern or 'process')}"]
        if plugin_name == "system.process.check":
            check = f"pgrep -f {_q(pattern or 'process')} >/dev/null"
            return [check if params.get("state", "present") == "present" else f"! {check}"]
        if plugin_name == "system.process.wait":
            return [f"timeout {_q(params.get('timeout', 60))} sh -c 'until pgrep -f {_q(pattern or 'process')} >/dev/null; do sleep {_q(params.get('interval', 2))}; done'"]

    if plugin_name.startswith("selinux."):
        if plugin_name == "security.selinux.boolean":
            return [f"{sudo}setsebool {'-P ' if params.get('persist', True) else ''}{_q(params.get('name', 'httpd_can_network_connect'))} {_q('on' if params.get('value', True) else 'off')}"]
        if plugin_name == "security.selinux.mode":
            return [f"{sudo}setenforce {_q(params.get('state', 'enforcing'))}"]
        if plugin_name in {"security.selinux.context", "security.selinux.fcontext"}:
            return [f"{sudo}semanage fcontext -a -t {_q(params.get('selinux_type', 'var_t'))} {_q(path)}"]
        if plugin_name == "security.selinux.restorecon":
            return [f"{sudo}restorecon {'-R ' if params.get('recursive') else ''}{_q(path)}"]

    if plugin_name == "security.ssh.authorized_key.add":
        return [f"{sudo}install -d -m 0700 ~{_q(params.get('user', name))}/.ssh && echo {_q(params.get('key', 'ssh-ed25519 AAAA demo'))} >> ~{_q(params.get('user', name))}/.ssh/authorized_keys"]
    if plugin_name == "security.sudo.dropin":
        return [f"{sudo}visudo -cf {_q(params.get('path', '/etc/sudoers'))}"]

    if plugin_name.startswith("data.transfer."):
        src = params.get("src", "/tmp/source")
        dest = params.get("dest", "/tmp/dest")
        if plugin_name == "data.transfer.download":
            return [f"scp{_ssh_opts(params)} {_q(str(src))} {_q(str(dest))}"]
        if plugin_name == "data.transfer.upload":
            return [f"scp{_ssh_opts(params)} {_q(str(src))} {_q(str(dest))}"]
            return [f"rsync -a {_q(str(src))}/ {_q(str(dest))}/"]

    if plugin_name in {"system.cron.entry.add", "system.cron.file"}:
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
