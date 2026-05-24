# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SSH client/server configuration and known_hosts plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


def _mapping_lines(values: Dict[str, Any]) -> str:
    return "".join(f"{key} {value}\n" for key, value in sorted(values.items()))


class SshConfigPlugin(BasePlugin):
    name = "ssh.config"
    description = "Install SSH client or sshd config drop-ins with backup and optional reload."
    required_params = ("name", "settings")
    optional_params = ("scope", "path", "match", "backup", "backup_suffix", "reload", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        if params.get("path"):
            return str(params["path"])
        scope = str(params.get("scope", "client"))
        name = str(params["name"])
        if not name.endswith(".conf"):
            name += ".conf"
        if scope == "server":
            return f"/etc/ssh/sshd_config.d/{name}"
        if scope == "client":
            return f"/etc/ssh/ssh_config.d/{name}"
        raise PluginValidationError("ssh.config scope must be client or server")

    def _content(self, params: Dict[str, Any]) -> str:
        settings = params.get("settings")
        if not isinstance(settings, dict) or not settings:
            raise PluginValidationError("ssh.config settings must be a non-empty mapping")
        lines = ["# Managed by automax\n"]
        if params.get("match"):
            lines.append(f"Match {params['match']}\n")
        lines.append(_mapping_lines(settings))
        return "".join(lines)

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _diff(self._path(params), self._content(params), "ssh-config-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        content = self._content(params)
        path = self._path(params)
        sudo = _sudo(params)
        temp = "/tmp/automax-ssh-config.$$"
        commands = [f"cat > {temp} <<'EOF'\n{content}EOF"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -D -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        if str(params.get("scope", "client")) == "server" and bool(params.get("reload", True)):
            commands.append(f"{sudo}sshd -t && ({sudo}systemctl reload sshd || {sudo}systemctl reload ssh)")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="ssh.config failed")


class SshKnownHostsPlugin(BasePlugin):
    name = "ssh.known_hosts"
    description = "Ensure a known_hosts entry exists or is removed on a remote target."
    required_params = ("host",)
    optional_params = ("key", "port", "path", "user", "state", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        if params.get("path"):
            return str(params["path"])
        if params.get("user"):
            return f"~{params['user']}/.ssh/known_hosts"
        return "$HOME/.ssh/known_hosts"

    def _entry(self, params: Dict[str, Any]) -> str:
        host = f"[{params['host']}]:{params['port']}" if params.get("port") else str(params["host"])
        if params.get("key"):
            return f"{host} {params['key']}"
        return host

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(self._path(params), self._entry(params) + "\n", "known-hosts-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("ssh.known_hosts state must be present or absent")
        path = self._path(params)
        host = str(params["host"])
        sudo = _sudo(params) if path.startswith("/etc/") else ""
        mkdir = f"mkdir -p $(dirname {quote(path)})"
        backup = f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}" if bool(params.get("backup", True)) else "true"
        if state == "absent":
            target = f"[{host}]:{params['port']}" if params.get("port") else host
            return [f"{mkdir} && {backup} && ssh-keygen -R {quote(target)} -f {quote(path)} >/dev/null 2>&1 || true"]
        if params.get("key"):
            entry = self._entry(params)
            return [f"{mkdir} && {backup} && touch {quote(path)} && grep -Fqx -- {quote(entry)} {quote(path)} || printf '%s\n' {quote(entry)} >> {quote(path)}"]
        port_arg = f" -p {quote(params['port'])}" if params.get("port") else ""
        return [f"{mkdir} && {backup} && ssh-keygen -R {quote(host)} -f {quote(path)} >/dev/null 2>&1 || true; ssh-keyscan{port_arg} {quote(host)} >> {quote(path)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="ssh.known_hosts failed")
