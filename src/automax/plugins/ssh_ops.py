# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SSH client/server configuration and known_hosts plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_file_expr, heredoc_to_stdin, shell_var_ref, tempfile_command, quote, result_from_remote, sudo_prefix



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
        sudo = sudo_prefix(params, default=True)
        temp_var = "automax_ssh_config_tmp"
        temp = shell_var_ref(temp_var)
        commands = [tempfile_command(temp_var, "ssh-config"), heredoc_to_file_expr(temp, content)]
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
    parameter_schema = {"user": {"type": "string", "description": "Remote user account owning known_hosts."}}
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
        sudo = sudo_prefix(params, default=True) if path.startswith("/etc/") else ""
        path_expr = "${HOME}/.ssh/known_hosts" if path == "$HOME/.ssh/known_hosts" else quote(path)
        mkdir = f'mkdir -p "$(dirname {path_expr})"'
        backup_dest = quote(path + str(params.get('backup_suffix', '.bak'))) if path != "$HOME/.ssh/known_hosts" else '"${HOME}/.ssh/known_hosts' + str(params.get('backup_suffix', '.bak')) + '"'
        backup = f"test ! -e {path_expr} || {sudo}cp -p {path_expr} {backup_dest}" if bool(params.get("backup", True)) else "true"
        if state == "absent":
            target = f"[{host}]:{params['port']}" if params.get("port") else host
            return [f"{mkdir} && {backup} && ssh-keygen -R {quote(target)} -f {path_expr} >/dev/null 2>&1 || true"]
        if params.get("key"):
            entry = self._entry(params)
            return [f"{mkdir} && {backup} && touch {path_expr} && grep -Fqx -- {quote(entry)} {path_expr} || printf '%s\n' {quote(entry)} >> {path_expr}"]
        port_arg = f" -p {quote(params['port'])}" if params.get("port") else ""
        return [f"{mkdir} && {backup} && ssh-keygen -R {quote(host)} -f {path_expr} >/dev/null 2>&1 || true; ssh-keyscan{port_arg} {quote(host)} >> {path_expr}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="ssh.known_hosts failed")


class SshKeygenPlugin(BasePlugin):
    name = "ssh.keygen"
    description = "Generate an SSH keypair on a remote target with idempotent overwrite protection."
    required_params = ("path",)
    optional_params = ("type", "bits", "comment", "force", "sudo", "owner", "group", "mode")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        key_type = str(params.get("type", "ed25519"))
        lines = [f"ssh-keygen -t {key_type} -f {params['path']}\n", f"public key: {params['path']}.pub\n"]
        return _diff(str(params["path"]), "".join(lines), "ssh-keygen-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = str(params["path"])
        key_type = str(params.get("type", "ed25519"))
        comment = str(params.get("comment", "automax"))
        sudo = sudo_prefix(params, default=True)
        force = bool(params.get("force", False))
        bits = f" -b {quote(params['bits'])}" if params.get("bits") else ""
        mode = str(params.get("mode", "0600"))
        commands = [
            f"{sudo}install -d -m 0700 \"$(dirname {quote(path)})\"",
            f"if test -e {quote(path)}; then {sudo + 'rm -f ' + quote(path) + ' ' + quote(path + '.pub') if force and sudo else 'rm -f ' + quote(path) + ' ' + quote(path + '.pub') if force else 'echo ' + quote('ssh key already exists: ' + path) + '; exit 0'}; fi",
            f"{sudo}ssh-keygen -q -t {quote(key_type)}{bits} -f {quote(path)} -N '' -C {quote(comment)}",
            f"{sudo}chmod {quote(mode)} {quote(path)}",
        ]
        owner = params.get("owner")
        group = params.get("group")
        if owner or group:
            spec = f"{owner or ''}:{group or ''}"
            commands.append(f"{sudo}chown {quote(spec)} {quote(path)} {quote(path + '.pub')}")
        commands.append(f"printf '%s\n' {quote(CHANGE_MARKER)}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ssh.keygen failed", data={"path": str(params["path"]), "public_key": str(params["path"]) + ".pub"})


class SshFingerprintPlugin(BasePlugin):
    name = "ssh.fingerprint"
    description = "Read an SSH public or private key fingerprint with ssh-keygen."
    required_params = ("path",)
    optional_params = ("algorithm", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "ssh.fingerprint is a read-only SSH key fingerprint query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        algorithm = str(params.get("algorithm", "sha256"))
        return [f"{sudo_prefix(params, default=True)}ssh-keygen -lf {quote(params['path'])} -E {quote(algorithm)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="ssh.fingerprint failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"fingerprint": out.strip()})


class SshPublicKeyPlugin(BasePlugin):
    name = "ssh.public_key"
    description = "Derive or read an SSH public key from a private key path."
    required_params = ("path",)
    optional_params = ("dest", "overwrite", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "ssh.public_key derives public key material; dest writes are shown in manual commands"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        command = f"{sudo_prefix(params, default=True)}ssh-keygen -y -f {quote(params['path'])}"
        if not params.get("dest"):
            return [command]
        guard = "" if bool(params.get("overwrite", False)) else f"test ! -e {quote(params['dest'])} && "
        if bool(params.get("sudo", True)):
            return [f"{guard}{command} | {sudo_prefix(params, default=True)}tee {quote(params['dest'])} >/dev/null"]
        return [f"{guard}{command} > {quote(params['dest'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="ssh.public_key failed")
        return PluginResult.success(changed=bool(params.get("dest")), rc=rc, stdout=out, stderr=err, data={"public_key": out.strip(), "dest": params.get("dest")})


class SshHostKeygenPlugin(BasePlugin):
    name = "ssh.host_keygen"
    description = "Generate missing OpenSSH host keys on a remote target."
    optional_params = ("types", "force", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "ssh.host_keygen creates host key material under the system SSH directory"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = sudo_prefix(params, default=True)
        types = params.get("types") or []
        if isinstance(types, str):
            types = [types]
        if not types:
            return [f"{sudo}ssh-keygen -A"]
        commands = []
        for key_type in types:
            path = f"/etc/ssh/ssh_host_{key_type}_key"
            if bool(params.get("force", False)):
                commands.append(f"{sudo}rm -f {quote(path)} {quote(path + '.pub')}")
            commands.append(f"test -e {quote(path)} || {sudo}ssh-keygen -q -t {quote(key_type)} -f {quote(path)} -N ''")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ssh.host_keygen failed")


class SshAuthorizedKeyAbsentPlugin(BasePlugin):
    name = "ssh.authorized_key_absent"
    description = "Remove one SSH authorized_keys line for a remote user."
    required_params = ("user", "key")
    optional_params = ("sudo",)
    parameter_schema = {"user": {"type": "string", "description": "Remote user account owning authorized_keys."}}
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "ssh.authorized_key_absent removes a specific authorized_keys line"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        script = r'''
set -eu
user=$1
key=$2
home=$(getent passwd "$user" | cut -d: -f6)
[ -n "$home" ] || { echo "user not found: $user" >&2; exit 1; }
auth_file="$home/.ssh/authorized_keys"
[ -e "$auth_file" ] || exit 0
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
grep -Fxv -- "$key" "$auth_file" > "$tmp" || true
if cmp -s "$tmp" "$auth_file"; then rm -f "$tmp"; exit 0; fi
cat "$tmp" > "$auth_file"
rm -f "$tmp"
echo __AUTOMAX_CHANGED__
'''
        return [
            heredoc_to_stdin(
                f"{sudo_prefix(params, default=True)}sh -s -- {quote(params['user'])} {quote(params['key'])}",
                script,
                prefix="AUTOMAX_SH",
            )
        ]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="ssh.authorized_key_absent failed")


class SshdValidatePlugin(BasePlugin):
    name = "sshd.validate"
    description = "Validate sshd configuration with sshd -t."
    optional_params = ("config", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "sshd.validate is a read-only sshd configuration validation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        config = f" -f {quote(params['config'])}" if params.get("config") else ""
        return [f"{sudo_prefix(params, default=True)}sshd -t{config}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="sshd.validate failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


def _ssh_keygen_passphrase(params: Dict[str, Any], context: ExecutionContext, *, masked: bool) -> str:
    if params.get("passphrase_secret"):
        if masked:
            return "***"
        secret_name = str(params["passphrase_secret"])
        if secret_name not in context.secrets:
            raise PluginValidationError(f"ssh.keygen passphrase_secret not found: {secret_name}")
        return str(context.secrets[secret_name])
    return ""


def _ssh_keygen_commands(self: SshKeygenPlugin, params: Dict[str, Any], context: ExecutionContext, *, masked: bool) -> list[str]:
    self.validate(params)
    path = str(params["path"])
    sudo = sudo_prefix(params, default=True)
    algorithm = str(params.get("algorithm", "sha256"))
    if bool(params.get("public_key_only", False)):
        commands = [f"test -f {quote(path + '.pub')} && cat {quote(path + '.pub')} || {sudo}ssh-keygen -y -f {quote(path)}"]
        if bool(params.get("fingerprint", False)):
            commands.append(f"{sudo}ssh-keygen -lf {quote(path + '.pub')} -E {quote(algorithm)}")
        return commands
    key_type = str(params.get("type", "ed25519"))
    comment = str(params.get("comment", "automax"))
    force = bool(params.get("force", False))
    bits = f" -b {quote(params['bits'])}" if params.get("bits") else ""
    mode = str(params.get("mode", "0600"))
    passphrase = _ssh_keygen_passphrase(params, context, masked=masked)
    commands = [
        f"{sudo}install -d -m 0700 \"$(dirname {quote(path)})\"",
        f"if test -e {quote(path)}; then {sudo + 'rm -f ' + quote(path) + ' ' + quote(path + '.pub') if force and sudo else 'rm -f ' + quote(path) + ' ' + quote(path + '.pub') if force else 'echo ' + quote('ssh key already exists: ' + path) + '; exit 0'}; fi",
        f"{sudo}ssh-keygen -q -t {quote(key_type)}{bits} -f {quote(path)} -N {quote(passphrase)} -C {quote(comment)}",
        f"{sudo}chmod {quote(mode)} {quote(path)}",
    ]
    owner = params.get("owner")
    group = params.get("group")
    if owner or group:
        spec = f"{owner or ''}:{group or ''}"
        commands.append(f"{sudo}chown {quote(spec)} {quote(path)} {quote(path + '.pub')}")
    if bool(params.get("fingerprint", True)):
        commands.append(f"{sudo}ssh-keygen -lf {quote(path + '.pub')} -E {quote(algorithm)}")
    commands.append(f"printf '%s\\n' {quote(CHANGE_MARKER)}")
    return [" && ".join(commands)]


def _ssh_keygen_manual(self: SshKeygenPlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    return _ssh_keygen_commands(self, params, context, masked=True)


def _ssh_keygen_execute(self: SshKeygenPlugin, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
    rc, out, err = exec_remote(context, _ssh_keygen_commands(self, params, context, masked=False)[0])
    return result_from_remote(rc=rc, stdout=out, stderr=err, message="ssh.keygen failed", data={"path": str(params["path"]), "public_key": str(params["path"]) + ".pub"})


SshKeygenPlugin.optional_params = ("type", "bits", "comment", "force", "passphrase_secret", "public_key_only", "fingerprint", "algorithm", "sudo", "owner", "group", "mode")
SshKeygenPlugin.manual_commands = _ssh_keygen_manual  # type: ignore[method-assign]
SshKeygenPlugin.execute = _ssh_keygen_execute  # type: ignore[method-assign]
