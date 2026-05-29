# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux prerequisite and host configuration plugins."""

from __future__ import annotations

from difflib import unified_diff
import json
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError, RenderedFileInstallMixin
from automax.plugins.remote_utils import cleanup_trap_command, CHANGE_MARKER, exec_remote, predicate_result_from_remote, heredoc_to_file_expr, heredoc_to_stdin, shell_var_ref, tempfile_command, tempfile_path_command, normalize_env_mapping, quote, render_env_prefix, result_from_remote, sudo_prefix



def _bool(value: Any) -> str:
    return "true" if bool(value) else "false"


def _lines_diff(path: str, desired: list[str], kind: str = "unified") -> list[Dict[str, Any]]:
    diff = "".join(unified_diff([], desired, fromfile=f"{path} (current)", tofile=f"{path} (desired)"))
    return [{"path": path, "diff": diff, "kind": kind}]


def _state_diff(path: str, current: str, desired: str, kind: str) -> list[Dict[str, Any]]:
    diff = "".join(
        unified_diff(
            [current if current.endswith("\n") else current + "\n"],
            [desired if desired.endswith("\n") else desired + "\n"],
            fromfile=f"{path} (current)",
            tofile=f"{path} (desired)",
        )
    )
    return [{"path": path, "diff": diff, "kind": kind}]


def _mapping(params: Dict[str, Any], key: str) -> dict[str, str]:
    raw = params.get(key, {}) or {}
    if not isinstance(raw, dict) or not raw:
        raise PluginValidationError(f"{key} must be a non-empty mapping")
    return normalize_env_mapping(raw)


class SwapPresentPlugin(BasePlugin):
    name = "storage.swap.add"
    description = "Ensure a swap file or swap device is active and optionally persisted in fstab."
    required_params = ("path",)
    optional_params = ("size", "persist", "opts", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _fstab_line(self, params: Dict[str, Any]) -> str:
        return f"{params['path']} none swap {params.get('opts', 'defaults')} 0 0"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        if not bool(params.get("persist", False)):
            return []
        return _lines_diff("/etc/fstab", [self._fstab_line(params) + "\n"], "fstab-plan")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.swap.add only changes runtime swap state unless persist=true"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = str(params["path"])
        sudo = sudo_prefix(params, default=True)
        commands = []
        if params.get("size"):
            commands.extend([
                f"test -e {quote(path)} || {sudo}fallocate -l {quote(params['size'])} {quote(path)}",
                f"{sudo}chmod 600 {quote(path)}",
                f"{sudo}mkswap {quote(path)}",
            ])
        commands.append(f"swapon --show=NAME --noheadings | grep -Fx -- {quote(path)} >/dev/null || {sudo}swapon {quote(path)}")
        if bool(params.get("persist", False)):
            opts = str(params.get("opts", "defaults"))
            if bool(params.get("backup", True)):
                commands.append(f"test ! -e /etc/fstab || {sudo}cp -p /etc/fstab /etc/fstab{quote(params.get('backup_suffix', '.bak'))}")
            line = f"{path} none swap {opts} 0 0"
            commands.append(f"grep -Fqx -- {quote(line)} /etc/fstab || printf '%s\\n' {quote(line)} | {sudo}tee -a /etc/fstab >/dev/null")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.swap.add failed")


class SwapAbsentPlugin(BasePlugin):
    name = "storage.swap.remove"
    description = "Disable a swap file or swap device and optionally remove its fstab entry."
    required_params = ("path",)
    optional_params = ("persist", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        if not bool(params.get("persist", False)):
            return []
        return _state_diff(
            "/etc/fstab",
            f"entries with first field {params['path']}",
            f"entries with first field {params['path']} removed",
            "fstab-plan",
        )

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.swap.remove only changes runtime swap state unless persist=true"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = str(params["path"])
        sudo = sudo_prefix(params, default=True)
        commands = [f"swapon --show=NAME --noheadings | grep -Fx -- {quote(path)} >/dev/null && {sudo}swapoff {quote(path)} || true"]
        if bool(params.get("persist", False)):
            if bool(params.get("backup", True)):
                commands.append(f"test ! -e /etc/fstab || {sudo}cp -p /etc/fstab /etc/fstab{quote(params.get('backup_suffix', '.bak'))}")
            commands.append(f"tmp=$(mktemp) && {cleanup_trap_command('tmp')} && awk '$1 != {quote(path)}' /etc/fstab > $tmp && {sudo}cp $tmp /etc/fstab")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.swap.remove failed")


class LimitsDropinPlugin(RenderedFileInstallMixin, BasePlugin):
    name = "os.limits.dropin"
    description = "Install an /etc/security/limits.d drop-in from structured entries."
    required_params = ("name", "entries")
    optional_params = ("backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "limits"

    def _content(self, params: Dict[str, Any]) -> str:
        entries = params.get("entries")
        if not isinstance(entries, list) or not entries:
            raise PluginValidationError("os.limits.dropin entries must be a non-empty list")
        lines = ["# Managed by automax\n"]
        for entry in entries:
            if not isinstance(entry, dict):
                raise PluginValidationError("os.limits.dropin entries must be mappings")
            lines.append("{domain} {type} {item} {value}\n".format(domain=entry["domain"], type=entry["type"], item=entry["item"], value=entry["value"]))
        return "".join(lines)

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return f"/etc/security/limits.d/{params['name']}.conf"

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._content(params)


class PamLimitsPlugin(BasePlugin):
    name = "security.pam.limits"
    description = "Ensure pam_limits.so is enabled in one or more PAM service files."
    required_params: tuple[str, ...] = ()
    optional_params = ("files", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _files(self, params: Dict[str, Any]) -> list[str]:
        files = params.get("files") or ["/etc/pam.d/login", "/etc/pam.d/sshd", "/etc/pam.d/su"]
        if isinstance(files, str):
            return [files]
        return [str(path) for path in files]

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        line = "session required pam_limits.so\n"
        return [_lines_diff(path, [line], "pam-plan")[0] for path in self._files(params)]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        files = self._files(params)
        sudo = sudo_prefix(params, default=True)
        commands = []
        line = "session required pam_limits.so"
        for path in files:
            if bool(params.get("backup", True)):
                commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(str(path) + str(params.get('backup_suffix', '.bak')))}")
            commands.append(f"grep -Eq '^session[[:space:]]+required[[:space:]]+pam_limits\\.so' {quote(path)} || printf '%s\\n' {quote(line)} | {sudo}tee -a {quote(path)} >/dev/null")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="security.pam.limits failed")


class HostsEntryPlugin(BasePlugin):
    name = "os.hosts.entry.add"
    description = "Ensure or remove an /etc/hosts entry with automatic pre-change backup."
    required_params = ("ip", "names")
    optional_params = ("state", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _line(self, params: Dict[str, Any]) -> str:
        names = params["names"]
        if isinstance(names, str):
            names = [names]
        return f"{params['ip']} {' '.join(str(name) for name in names)}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        state = str(params.get("state", "present"))
        desired = [] if state == "absent" else [self._line(params) + "\n"]
        return _lines_diff("/etc/hosts", desired)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("os.hosts.entry.add state must be present or absent")
        sudo = sudo_prefix(params, default=True)
        line = self._line(params)
        commands = []
        if bool(params.get("backup", True)):
            commands.append(f"{sudo}cp -p /etc/hosts /etc/hosts{quote(params.get('backup_suffix', '.bak'))}")
        if state == "present":
            commands.append(f"grep -Fqx -- {quote(line)} /etc/hosts || printf '%s\\n' {quote(line)} | {sudo}tee -a /etc/hosts >/dev/null")
        else:
            commands.append(f"tmp=$(mktemp); {cleanup_trap_command('tmp')}; grep -Fxv -- {quote(line)} /etc/hosts > $tmp || true; {sudo}cp $tmp /etc/hosts")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="os.hosts.entry.add failed")


class HostnameSetPlugin(BasePlugin):
    name = "os.hostname.set"
    description = "Set the system hostname with hostnamectl."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _state_diff("hostname", "current hostname", str(params["name"]), "hostname-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"test \"$(hostnamectl --static 2>/dev/null || hostname)\" = {quote(params['name'])} || {sudo_prefix(params, default=True)}hostnamectl set-hostname {quote(params['name'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="os.hostname.set failed")


class NetworkDnsFactsPlugin(BasePlugin):
    name = "network.dns.facts"
    description = "Detect the active DNS resolver backend without changing resolver configuration."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "network.dns.facts is read-only resolver backend detection and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        script = '''
set -eu
backend=plain-file
path=/etc/resolv.conf
target=
if [ -L "$path" ]; then
  target=$(readlink -f "$path" || true)
  case "$target" in
    *systemd/resolve*) backend=systemd-resolved ;;
    *NetworkManager*) backend=networkmanager ;;
    *) backend=symlink ;;
  esac
elif [ -d /etc/resolvconf ]; then backend=resolvconf
elif command -v resolvectl >/dev/null 2>&1; then backend=systemd-resolved
elif command -v nmcli >/dev/null 2>&1; then backend=networkmanager
fi
printf 'backend=%s\npath=%s\ntarget=%s\n' "$backend" "$path" "$target"
'''
        return [heredoc_to_stdin("sh -s", script, prefix="AUTOMAX_SH")]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="network.dns.facts failed")
        data = {}
        for line in out.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key] = value
        return PluginResult.success(changed=False, stdout=out, stderr=err, data=data)


class NetworkDnsConfigBase(RenderedFileInstallMixin, BasePlugin):
    description = "Manage DNS resolver settings safely using explicit plain-file, systemd-resolved, NetworkManager or resolvconf backends."
    required_params: tuple[str, ...] = ()
    optional_params = ("backend", "nameservers", "search", "options", "path", "nm_connection", "force", "backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "resolver"
    rendered_file_diff_kind = "resolver-plan"

    def _nameservers(self, params: Dict[str, Any]) -> list[str]:
        values = params.get("nameservers", []) or []
        if isinstance(values, str):
            values = [values]
        return [str(value) for value in values]

    def _search(self, params: Dict[str, Any]) -> list[str]:
        values = params.get("search", []) or []
        if isinstance(values, str):
            values = [values]
        return [str(value) for value in values]

    def _options(self, params: Dict[str, Any]) -> list[str]:
        values = params.get("options", []) or []
        if isinstance(values, str):
            values = [values]
        return [str(value) for value in values]

    def _content(self, params: Dict[str, Any]) -> str:
        lines = ["# Managed by automax\n"]
        for ns in self._nameservers(params):
            lines.append(f"nameserver {ns}\n")
        search = self._search(params)
        if search:
            lines.append("search " + " ".join(search) + "\n")
        for option in self._options(params):
            lines.append(f"options {option}\n")
        return "".join(lines)

    def _resolved_content(self, params: Dict[str, Any]) -> str:
        lines = ["# Managed by automax\n", "[Resolve]\n"]
        if self._nameservers(params):
            lines.append("DNS=" + " ".join(self._nameservers(params)) + "\n")
        if self._search(params):
            lines.append("Domains=" + " ".join(self._search(params)) + "\n")
        return "".join(lines)

    def _backend(self, params: Dict[str, Any]) -> str:
        backend = str(params.get("backend", "plain-file"))
        if backend == "auto":
            raise PluginValidationError("network.dns.config requires an explicit backend for persistent changes")
        if backend not in {"plain-file", "systemd-resolved", "networkmanager", "resolvconf"}:
            raise PluginValidationError("resolver backend must be plain-file, systemd-resolved, networkmanager or resolvconf")
        return backend

    def _path_for_backend(self, params: Dict[str, Any]) -> str:
        backend = self._backend(params)
        if params.get("path"):
            return str(params["path"])
        if backend == "systemd-resolved":
            return "/etc/systemd/resolved.conf.d/99-automax.conf"
        if backend == "resolvconf":
            return "/etc/resolvconf/resolv.conf.d/head"
        return "/etc/resolv.conf"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        backend = self._backend(params)
        if backend == "networkmanager":
            desired = f"connection={params.get('nm_connection', '<required>')} dns={','.join(self._nameservers(params))} search={','.join(self._search(params))}"
            return _state_diff("NetworkManager DNS", "current connection DNS", desired, "resolver-plan")
        return RenderedFileInstallMixin.diff_preview(self, params, context)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        backend = self._backend(params)
        sudo = sudo_prefix(params, default=True)
        if backend == "networkmanager":
            connection = params.get("nm_connection")
            if not connection:
                raise PluginValidationError("network.dns.config backend=networkmanager requires nm_connection")
            dns = " ".join(self._nameservers(params))
            search = " ".join(self._search(params))
            commands = [f"{sudo}nmcli connection modify {quote(connection)} ipv4.ignore-auto-dns yes"]
            if dns:
                commands.append(f"{sudo}nmcli connection modify {quote(connection)} ipv4.dns {quote(dns)}")
            if search:
                commands.append(f"{sudo}nmcli connection modify {quote(connection)} ipv4.dns-search {quote(search)}")
            commands.append(f"{sudo}nmcli connection up {quote(connection)}")
            return commands
        return RenderedFileInstallMixin.manual_commands(self, params, context)

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path_for_backend(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._resolved_content(params) if self._backend(params) == "systemd-resolved" else self._content(params)

    def rendered_file_validate_commands(self, params: Dict[str, Any], context: ExecutionContext, temp_path: str) -> list[str]:
        if self._backend(params) == "plain-file" and not bool(params.get("force", False)):
            return ["if [ -L /etc/resolv.conf ]; then echo 'refusing to manage symlinked /etc/resolv.conf with backend=plain-file' >&2; exit 1; fi"]
        return []

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        backend = self._backend(params)
        sudo = self.rendered_file_sudo(params)
        if backend == "systemd-resolved":
            return [f"{sudo}systemctl restart systemd-resolved"]
        if backend == "resolvconf":
            return [f"{sudo}resolvconf -u"]
        return []


class ChronyServersPlugin(RenderedFileInstallMixin, BasePlugin):
    name = "os.time.chrony.servers.set"
    description = "Install a chrony server drop-in and optionally restart chronyd."
    required_params = ("servers",)
    optional_params = ("path", "backup", "backup_suffix", "reload", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "chrony"

    def _content(self, params: Dict[str, Any]) -> str:
        servers = params.get("servers")
        if isinstance(servers, str):
            servers = [servers]
        if not isinstance(servers, list) or not servers:
            raise PluginValidationError("os.time.chrony.servers.set requires a non-empty servers list")
        return "# Managed by automax\n" + "".join(f"server {server} iburst\n" for server in servers)

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", "/etc/chrony.d/99-automax.conf"))

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._content(params)

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if bool(params.get("reload", True)):
            sudo = self.rendered_file_sudo(params)
            return [f"{sudo}systemctl restart chronyd || {sudo}systemctl restart chrony"]
        return []


class ChronySourcesAssertPlugin(BasePlugin):
    name = "os.time.chrony.sources.check"
    description = "Check whether chrony has usable sources and print tracking/source status."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "os.time.chrony.sources.check is a read-only predicate and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return ["chronyc tracking && chronyc sources -v"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.time.chrony.sources.check failed",
            data_key="usable",
        )


class EnvSetPlugin(BasePlugin):
    name = "os.env.set"
    description = "Set step-scoped or persistent shell environment variables."
    required_params = ("variables",)
    optional_params = ("scope", "path", "user", "backup", "backup_suffix", "sudo")
    parameter_schema = {"user": {"type": "string", "description": "User account name for scope=user."}}
    opens_remote_session = True

    def _content(self, params: Dict[str, Any]) -> str:
        variables = _mapping(params, "variables")
        return "# Managed by automax\n" + "".join(f"export {name}={quote(value)}\n" for name, value in sorted(variables.items()))

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        if str(params.get("scope", "step")) == "step":
            context.step_state.setdefault("env", {}).update(_mapping(params, "variables"))
        return PluginResult.success(changed=False, message="dry-run: os.env.set", data={"scope": params.get("scope", "step")})

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        scope = str(params.get("scope", "step"))
        if scope == "step":
            return []
        return _lines_diff(self._path(params), self._content(params).splitlines(keepends=True))

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "step-scoped environment variables do not modify files"

    def _path(self, params: Dict[str, Any]) -> str:
        scope = str(params.get("scope", "step"))
        if params.get("path"):
            return str(params["path"])
        if scope == "global":
            return "/etc/profile.d/automax.sh"
        if scope == "user":
            user = str(params.get("user", "$USER"))
            return f"~{user}/.automax_env" if user != "$USER" else "$HOME/.automax_env"
        raise PluginValidationError("os.env.set persistent scopes require scope=global, scope=user or path")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        variables = _mapping(params, "variables")
        scope = str(params.get("scope", "step"))
        if scope == "step":
            return [f"export {render_env_prefix(variables)}"]
        content = self._content(params)
        path = self._path(params)
        sudo = sudo_prefix(params, default=scope == "global")
        temp_var = "automax_env_tmp"
        temp = shell_var_ref(temp_var)
        commands = [tempfile_command(temp_var, "env"), cleanup_trap_command(temp_var), heredoc_to_file_expr(temp, content)]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        scope = str(params.get("scope", "step"))
        if scope == "step":
            context.step_state.setdefault("env", {}).update(_mapping(params, "variables"))
            return PluginResult.success(changed=False, data={"scope": scope, "variables": sorted(_mapping(params, "variables"))})
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="os.env.set failed")


class SystemRebootPlugin(BasePlugin):
    name = "system.reboot"
    description = "Reboot a remote server, optionally waiting until SSH comes back."
    required_params: tuple[str, ...] = ()
    optional_params = ("wait", "delay", "timeout", "connect_timeout", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "system.reboot changes remote runtime state and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        delay = int(params.get("delay", 3))
        return [f"({sudo_prefix(params, default=True)}shutdown -r +0 'Automax requested reboot' >/dev/null 2>&1 &) && sleep {delay}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="system.reboot failed")
        # The engine owns SSH connections; waiting for reconnect is intentionally reported as operator command here.
        return PluginResult.success(changed=True, rc=rc, stdout=out, stderr=err, message="reboot requested")


class DownloadFilePlugin(BasePlugin):
    name = "data.download.url"
    description = "Download a URL on the remote target using curl or wget, with optional checksum and backup."
    required_params = ("url", "dest")
    optional_params = ("checksum", "force", "backup", "backup_suffix", "mode", "owner", "group", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = [
            f"url: {params['url']}\n",
            f"dest: {params['dest']}\n",
            f"checksum: {params.get('checksum', '-')}\n",
            f"backup: {bool(params.get('backup', True))}\n",
            f"force: {bool(params.get('force', False))}\n",
        ]
        return _lines_diff(str(params["dest"]), desired, "download-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
        dest = str(params["dest"])
        tmp_var = "automax_download_tmp"
        tmp = shell_var_ref(tmp_var)
        commands = [
            tempfile_path_command(tmp_var, f"{dest}.automax-download.XXXXXX"),
            cleanup_trap_command(tmp_var),
            f"(curl -fsSL --retry 3 -o {tmp} {quote(params['url'])} || wget -q -O {tmp} {quote(params['url'])})"
        ]
        if params.get("checksum"):
            commands.append(f"printf '%s  %s\\n' {quote(params['checksum'])} {tmp} | sha256sum -c -")
        if bool(params.get("backup", True)):
            commands.append(
                f"(test ! -e {quote(dest)} || {sudo}cp -p {quote(dest)} {quote(dest + str(params.get('backup_suffix', '.bak')))})"
            )
        if not bool(params.get("force", False)):
            commands.append(f"(test ! -e {quote(dest)} || cmp -s {tmp} {quote(dest)})")
        commands.append(f"{sudo}install {('-m ' + quote(params['mode'])) if params.get('mode') else ''} {tmp} {quote(dest)}".replace("  ", " "))
        if params.get("owner") or params.get("group"):
            owner = str(params.get("owner", ""))
            group = str(params.get("group", ""))
            spec = f"{owner}:{group}" if group else owner
            commands.append(f"{sudo}chown {quote(spec)} {quote(dest)}")
        commands.append(f"rm -f {tmp}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="data.download.url failed")


class HostsEntryRemovePlugin(HostsEntryPlugin):
    name = "os.hosts.entry.remove"
    description = "Remove an exact /etc/hosts entry with automatic pre-change backup."

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        copied = dict(params)
        copied["state"] = "absent"
        return super().manual_commands(copied, context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="os.hosts.entry.remove failed")


class HostsEntryCheckPlugin(HostsEntryPlugin):
    name = "os.hosts.entry.check"
    description = "Check whether an exact /etc/hosts entry is present."
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "os.hosts.entry.check is a read-only /etc/hosts predicate"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"grep -Fqx -- {quote(self._line(params))} /etc/hosts"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.hosts.entry.check failed",
            data_key="exists",
            data={"entry": self._line(params)},
        )


class HostsFactsPlugin(BasePlugin):
    name = "os.hosts.facts"
    description = "Read /etc/hosts entries as structured facts."
    optional_params = ("path", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "os.hosts.facts is a read-only /etc/hosts inventory query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        path = quote(params.get("path", "/etc/hosts"))
        script = r'''
import json, sys
entries = []
with open(sys.argv[1], encoding='utf-8', errors='replace') as fh:
    for raw in fh:
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            entries.append({'ip': parts[0], 'names': parts[1:]})
print(json.dumps({'hosts': entries}, sort_keys=True))
'''
        return [heredoc_to_stdin(f"python3 - {path}", script, prefix="AUTOMAX_PY")]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.hosts.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data=json.loads(out or "{}"))


class HostnameGetPlugin(BasePlugin):
    name = "os.hostname.get"
    description = "Read the current static hostname."
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "os.hostname.get is a read-only hostname query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return ["hostnamectl --static 2>/dev/null || hostname"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.hostname.get failed", data={"hostname": out.strip()})


class HostnameCheckPlugin(HostnameGetPlugin):
    name = "os.hostname.check"
    description = "Check whether the current static hostname matches."
    required_params = ("name",)
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"test \"$(hostnamectl --static 2>/dev/null || hostname)\" = {quote(params['name'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.hostname.check failed",
            data_key="matches",
            data={"expected": str(params["name"])},
        )


class EnvGetPlugin(BasePlugin):
    name = "os.env.get"
    description = "Read one environment variable from the remote shell context."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"printenv {quote(params['name'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.env.get failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"name": str(params["name"]), "value": out.rstrip("\n")})


class EnvCheckPlugin(EnvGetPlugin):
    name = "os.env.check"
    description = "Check whether one environment variable has the expected value in the remote shell context."
    required_params = ("name", "value")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"test \"$(printenv {quote(params['name'])})\" = {quote(params['value'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.env.check failed",
            data_key="matches",
            data={"name": str(params["name"])},
        )


class EnvFactsPlugin(BasePlugin):
    name = "os.env.facts"
    description = "Read the remote shell environment as key/value facts."
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return ["env"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, "env")
        values = {}
        for line in out.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.env.facts failed", data={"env": values})


class EnvRemovePlugin(BasePlugin):
    name = "os.env.remove"
    description = "Remove a managed persistent shell environment file or unset step-scoped variables."
    optional_params = ("name", "names", "scope", "path", "user", "sudo")
    opens_remote_session = True

    def _names(self, params: Dict[str, Any]) -> list[str]:
        raw = params.get("names", params.get("name"))
        if raw is None:
            raise PluginValidationError("os.env.remove requires name or names")
        return [str(item) for item in (raw if isinstance(raw, list) else [raw])]

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        if str(params.get("scope", "step")) == "step":
            for name in self._names(params):
                context.step_state.setdefault("env", {}).pop(name, None)
        return PluginResult.success(changed=False, message="dry-run: os.env.remove", data={"scope": params.get("scope", "step")})

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        scope = str(params.get("scope", "step"))
        names = self._names(params)
        if scope == "step":
            return ["unset " + " ".join(quote(name) for name in names)]
        copied = dict(params)
        path = EnvSetPlugin()._path(copied)
        sudo = sudo_prefix(params, default=scope == "global")
        pattern = "\\|".join(names)
        return [f"if test -e {quote(path)}; then {sudo}sed -i -E '/^export[[:space:]]+({pattern})=/d' {quote(path)} && echo {CHANGE_MARKER}; fi"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        scope = str(params.get("scope", "step"))
        if scope == "step":
            for name in self._names(params):
                context.step_state.setdefault("env", {}).pop(name, None)
            return PluginResult.success(changed=False, data={"scope": scope, "removed": self._names(params)})
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.env.remove failed")


class ChronyServersGetPlugin(BasePlugin):
    name = "os.time.chrony.servers.get"
    description = "Read configured chrony server lines from chrony configuration."
    optional_params = ("path", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        path = quote(params.get("path", "/etc/chrony.d/99-automax.conf"))
        return [f"test -e {path} && awk '/^[[:space:]]*server[[:space:]]+/ {{print $2}}' {path} || true"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        servers = [line.strip() for line in out.splitlines() if line.strip()]
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.time.chrony.servers.get failed", data={"servers": servers})


class ChronyServersCheckPlugin(ChronyServersGetPlugin):
    name = "os.time.chrony.servers.check"
    description = "Check whether configured chrony server lines exist in the managed chrony drop-in."
    required_params = ("servers",)
    optional_params = ("path", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        servers = params["servers"] if isinstance(params["servers"], list) else [params["servers"]]
        path = quote(params.get("path", "/etc/chrony.d/99-automax.conf"))
        checks = [f"grep -Eq '^[[:space:]]*server[[:space:]]+{quote(server)}([[:space:]]|$)' {path}" for server in servers]
        return [" && ".join(checks)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.time.chrony.servers.check failed",
            data_key="matches",
        )
