# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux prerequisite and host configuration plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any], default: bool = True) -> str:
    return "sudo -n " if bool(params.get("sudo", default)) else ""


def _bool(value: Any) -> str:
    return "true" if bool(value) else "false"


def _lines_diff(path: str, desired: list[str], kind: str = "unified") -> list[Dict[str, Any]]:
    diff = "".join(unified_diff([], desired, fromfile=f"{path} (current)", tofile=f"{path} (desired)"))
    return [{"path": path, "diff": diff, "kind": kind}]


def _mapping(params: Dict[str, Any], key: str) -> dict[str, str]:
    raw = params.get(key, {}) or {}
    if not isinstance(raw, dict) or not raw:
        raise PluginValidationError(f"{key} must be a non-empty mapping")
    return {str(name): str(value) for name, value in raw.items()}


class SwapPresentPlugin(BasePlugin):
    name = "swap.present"
    description = "Ensure a swap file or swap device is active and optionally persisted in fstab."
    required_params = ("path",)
    optional_params = ("size", "persist", "opts", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = str(params["path"])
        sudo = _sudo(params)
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
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="swap.present failed")


class SwapAbsentPlugin(BasePlugin):
    name = "swap.absent"
    description = "Disable a swap file or swap device and optionally remove its fstab entry."
    required_params = ("path",)
    optional_params = ("persist", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = str(params["path"])
        sudo = _sudo(params)
        commands = [f"swapon --show=NAME --noheadings | grep -Fx -- {quote(path)} >/dev/null && {sudo}swapoff {quote(path)} || true"]
        if bool(params.get("persist", False)):
            if bool(params.get("backup", True)):
                commands.append(f"test ! -e /etc/fstab || {sudo}cp -p /etc/fstab /etc/fstab{quote(params.get('backup_suffix', '.bak'))}")
            commands.append(f"tmp=$(mktemp) && awk '$1 != {quote(path)}' /etc/fstab > $tmp && {sudo}cp $tmp /etc/fstab && rm -f $tmp")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="swap.absent failed")


class LimitsDropinPlugin(BasePlugin):
    name = "limits.dropin"
    description = "Install an /etc/security/limits.d drop-in from structured entries."
    required_params = ("name", "entries")
    optional_params = ("backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _content(self, params: Dict[str, Any]) -> str:
        entries = params.get("entries")
        if not isinstance(entries, list) or not entries:
            raise PluginValidationError("limits.dropin entries must be a non-empty list")
        lines = ["# Managed by automax\n"]
        for entry in entries:
            if not isinstance(entry, dict):
                raise PluginValidationError("limits.dropin entries must be mappings")
            lines.append("{domain} {type} {item} {value}\n".format(domain=entry["domain"], type=entry["type"], item=entry["item"], value=entry["value"]))
        return "".join(lines)

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _lines_diff(f"/etc/security/limits.d/{params['name']}.conf", self._content(params).splitlines(keepends=True))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        content = self._content(params)
        path = f"/etc/security/limits.d/{params['name']}.conf"
        sudo = _sudo(params)
        temp = "/tmp/automax-limits.$$"
        commands = [f"cat > {temp} <<'EOF'\n{content}EOF"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="limits.dropin failed")


class PamLimitsPlugin(BasePlugin):
    name = "pam.limits"
    description = "Ensure pam_limits.so is enabled in one or more PAM service files."
    required_params: tuple[str, ...] = ()
    optional_params = ("files", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        files = params.get("files") or ["/etc/pam.d/login", "/etc/pam.d/sshd", "/etc/pam.d/su"]
        if isinstance(files, str):
            files = [files]
        sudo = _sudo(params)
        commands = []
        line = "session required pam_limits.so"
        for path in files:
            if bool(params.get("backup", True)):
                commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(str(path) + str(params.get('backup_suffix', '.bak')))}")
            commands.append(f"grep -Eq '^session[[:space:]]+required[[:space:]]+pam_limits\\.so' {quote(path)} || printf '%s\\n' {quote(line)} | {sudo}tee -a {quote(path)} >/dev/null")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pam.limits failed")


class HostsEntryPlugin(BasePlugin):
    name = "hosts.entry"
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
            raise PluginValidationError("hosts.entry state must be present or absent")
        sudo = _sudo(params)
        line = self._line(params)
        commands = []
        if bool(params.get("backup", True)):
            commands.append(f"{sudo}cp -p /etc/hosts /etc/hosts{quote(params.get('backup_suffix', '.bak'))}")
        if state == "present":
            commands.append(f"grep -Fqx -- {quote(line)} /etc/hosts || printf '%s\\n' {quote(line)} | {sudo}tee -a /etc/hosts >/dev/null")
        else:
            commands.append(f"tmp=$(mktemp) && grep -Fxv -- {quote(line)} /etc/hosts > $tmp || true; {sudo}cp $tmp /etc/hosts; rm -f $tmp")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="hosts.entry failed")


class HostnameSetPlugin(BasePlugin):
    name = "hostname.set"
    description = "Set the system hostname with hostnamectl."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"test \"$(hostnamectl --static 2>/dev/null || hostname)\" = {quote(params['name'])} || {_sudo(params)}hostnamectl set-hostname {quote(params['name'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="hostname.set failed")


class ResolverConfigPlugin(BasePlugin):
    name = "resolver.config"
    description = "Manage resolver configuration safely, refusing unmanaged /etc/resolv.conf ownership mismatches by default."
    required_params: tuple[str, ...] = ()
    optional_params = ("backend", "nameservers", "search", "options", "path", "force", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _content(self, params: Dict[str, Any]) -> str:
        lines = ["# Managed by automax\n"]
        for ns in params.get("nameservers", []) or []:
            lines.append(f"nameserver {ns}\n")
        search = params.get("search", []) or []
        if isinstance(search, str):
            search = [search]
        if search:
            lines.append("search " + " ".join(str(item) for item in search) + "\n")
        for option in params.get("options", []) or []:
            lines.append(f"options {option}\n")
        return "".join(lines)

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        path = str(params.get("path", "/etc/resolv.conf"))
        return _lines_diff(path, self._content(params).splitlines(keepends=True))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        content = self._content(params)
        backend = str(params.get("backend", "auto"))
        path = str(params.get("path", "/etc/resolv.conf"))
        sudo = _sudo(params)
        temp = "/tmp/automax-resolver.$$"
        guard = ""
        if backend == "auto" and not bool(params.get("force", False)):
            guard = "if [ -L /etc/resolv.conf ]; then echo 'refusing to manage symlinked /etc/resolv.conf without backend or force' >&2; exit 1; fi && "
        commands = [f"cat > {temp} <<'EOF'\n{content}EOF"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{guard}{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="resolver.config failed")


class ChronyServersPlugin(BasePlugin):
    name = "chrony.servers"
    description = "Install a chrony server drop-in and optionally restart chronyd."
    required_params = ("servers",)
    optional_params = ("path", "backup", "backup_suffix", "reload", "sudo")
    opens_remote_session = True

    def _content(self, params: Dict[str, Any]) -> str:
        servers = params.get("servers")
        if isinstance(servers, str):
            servers = [servers]
        if not isinstance(servers, list) or not servers:
            raise PluginValidationError("chrony.servers requires a non-empty servers list")
        return "# Managed by automax\n" + "".join(f"server {server} iburst\n" for server in servers)

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        path = str(params.get("path", "/etc/chrony.d/99-automax.conf"))
        return _lines_diff(path, self._content(params).splitlines(keepends=True))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        content = self._content(params)
        path = str(params.get("path", "/etc/chrony.d/99-automax.conf"))
        sudo = _sudo(params)
        temp = "/tmp/automax-chrony.$$"
        commands = [f"cat > {temp} <<'EOF'\n{content}EOF"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        if bool(params.get("reload", True)):
            commands.append(f"{sudo}systemctl restart chronyd || {sudo}systemctl restart chrony")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="chrony.servers failed")


class ChronySourcesAssertPlugin(BasePlugin):
    name = "chrony.sources_assert"
    description = "Assert chrony has usable sources and print tracking/source status."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return ["chronyc tracking && chronyc sources -v"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="chrony.sources_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class EnvSetPlugin(BasePlugin):
    name = "env.set"
    description = "Set step-scoped or persistent shell environment variables."
    required_params = ("variables",)
    optional_params = ("scope", "path", "user", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _content(self, params: Dict[str, Any]) -> str:
        variables = _mapping(params, "variables")
        return "# Managed by automax\n" + "".join(f"export {name}={quote(value)}\n" for name, value in sorted(variables.items()))

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        if str(params.get("scope", "step")) == "step":
            context.step_state.setdefault("env", {}).update(_mapping(params, "variables"))
        return PluginResult.success(changed=False, message="dry-run: env.set", data={"scope": params.get("scope", "step")})

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
        raise PluginValidationError("env.set persistent scopes require scope=global, scope=user or path")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        variables = _mapping(params, "variables")
        scope = str(params.get("scope", "step"))
        if scope == "step":
            exports = " ".join(f"{name}={quote(value)}" for name, value in sorted(variables.items()))
            return [f"export {exports}"]
        content = self._content(params)
        path = self._path(params)
        sudo = _sudo(params, default=scope == "global")
        temp = "/tmp/automax-env.$$"
        commands = [f"cat > {temp} <<'EOF'\n{content}EOF"]
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
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="env.set failed")


class SystemRebootPlugin(BasePlugin):
    name = "system.reboot"
    description = "Reboot a remote server, optionally waiting until SSH comes back."
    required_params: tuple[str, ...] = ()
    optional_params = ("wait", "delay", "timeout", "connect_timeout", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        delay = int(params.get("delay", 3))
        return [f"({_sudo(params)}shutdown -r +0 'Automax requested reboot' >/dev/null 2>&1 &) && sleep {delay}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="system.reboot failed")
        # The engine owns SSH connections; waiting for reconnect is intentionally reported as operator command here.
        return PluginResult.success(changed=True, rc=rc, stdout=out, stderr=err, message="reboot requested")


class DownloadFilePlugin(BasePlugin):
    name = "download.file"
    description = "Download a URL on the remote target using curl or wget, with optional checksum and backup."
    required_params = ("url", "dest")
    optional_params = ("checksum", "force", "backup", "backup_suffix", "mode", "owner", "group", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        dest = str(params["dest"])
        tmp = f"{dest}.automax-download.$$"
        commands = [f"curl -fL --retry 3 -o {quote(tmp)} {quote(params['url'])} || wget -O {quote(tmp)} {quote(params['url'])}"]
        if params.get("checksum"):
            commands.append(f"printf '%s  %s\\n' {quote(params['checksum'])} {quote(tmp)} | sha256sum -c -")
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(dest)} || {sudo}cp -p {quote(dest)} {quote(dest + str(params.get('backup_suffix', '.bak')))}")
        if not bool(params.get("force", False)):
            commands.append(f"test ! -e {quote(dest)} || cmp -s {quote(tmp)} {quote(dest)}")
        commands.append(f"{sudo}install {('-m ' + quote(params['mode'])) if params.get('mode') else ''} {quote(tmp)} {quote(dest)}".replace("  ", " "))
        if params.get("owner") or params.get("group"):
            owner = str(params.get("owner", ""))
            group = str(params.get("group", ""))
            spec = f"{owner}:{group}" if group else owner
            commands.append(f"{sudo}chown {quote(spec)} {quote(dest)}")
        commands.append(f"rm -f {quote(tmp)}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="download.file failed")
