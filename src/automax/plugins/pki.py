# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Certificate and PKI operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _content(params: Dict[str, Any]) -> str:
    if params.get("content") is not None:
        return str(params["content"])
    if params.get("src"):
        return Path(str(params["src"])).expanduser().read_text(encoding=str(params.get("encoding", "utf-8")))
    raise PluginValidationError("pki.ca_install requires content or src")


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class PkiCaInstallPlugin(BasePlugin):
    name = "pki.ca_install"
    description = "Install a CA certificate into an explicit path or a distro-native system trust store."
    required_params: tuple[str, ...] = ()
    optional_params = ("dest", "name", "trust_store", "src", "content", "mode", "owner", "group", "backup", "backup_suffix", "update_trust", "sudo", "encoding")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _content(params)
        if not params.get("dest") and not params.get("name"):
            raise PluginValidationError("pki.ca_install requires dest or name")

    def _dest(self, params: Dict[str, Any], flavor: str = "debian") -> str:
        if params.get("dest"):
            return str(params["dest"])
        name = str(params["name"])
        filename = name if name.endswith(".crt") else f"{name}.crt"
        if flavor == "redhat":
            return f"/etc/pki/ca-trust/source/anchors/{filename}"
        return f"/usr/local/share/ca-certificates/{filename}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        if str(params.get("trust_store", "explicit")) == "system" and not params.get("dest"):
            return _diff("system trust store", _content(params), "pki-plan")
        return _diff(self._dest(params), _content(params), "pki-plan")

    def _install_cmd(self, params: Dict[str, Any], dest: str) -> str:
        content = _content(params)
        sudo = _sudo(params)
        temp = "/tmp/automax-ca.$$"
        commands = [f"cat > {temp} <<'EOF'\n{content}\nEOF"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(dest)} || {sudo}cp -p {quote(dest)} {quote(dest + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -D -m {quote(params.get('mode', '0644'))} {temp} {quote(dest)}")
        if params.get("owner") or params.get("group"):
            owner = str(params.get("owner", ""))
            group = str(params.get("group", ""))
            commands.append(f"{sudo}chown {quote(owner + ':' + group)} {quote(dest)}")
        commands.append(f"rm -f {temp}")
        return " && ".join(commands)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        if str(params.get("trust_store", "explicit")) == "system" and not params.get("dest"):
            deb = self._install_cmd(params, self._dest(params, "debian")) + f" && {sudo}update-ca-certificates"
            rh = self._install_cmd(params, self._dest(params, "redhat")) + f" && {sudo}update-ca-trust extract"
            return [f"if command -v update-ca-certificates >/dev/null 2>&1; then {deb}; elif command -v update-ca-trust >/dev/null 2>&1; then {rh}; else echo 'no supported system CA trust store found' >&2; exit 1; fi"]
        commands = [self._install_cmd(params, self._dest(params))]
        if bool(params.get("update_trust", True)):
            commands.append(f"if command -v update-ca-certificates >/dev/null 2>&1; then {sudo}update-ca-certificates; elif command -v update-ca-trust >/dev/null 2>&1; then {sudo}update-ca-trust extract; fi")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pki.ca_install failed")


class PkiKeyPermissionsPlugin(BasePlugin):
    name = "pki.key_permissions"
    description = "Enforce owner/group/mode on a private key or certificate file."
    required_params = ("path",)
    optional_params = ("owner", "group", "mode", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = f"owner={params.get('owner', '')} group={params.get('group', '')} mode={params.get('mode', '')}"
        return _diff(str(params["path"]), desired + "\n", "pki-permissions-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        path = quote(params["path"])
        commands = []
        if params.get("owner") or params.get("group"):
            commands.append(f"{sudo}chown {quote(str(params.get('owner', '')) + ':' + str(params.get('group', '')))} {path}")
        if params.get("mode"):
            commands.append(f"{sudo}chmod {quote(params['mode'])} {path}")
        return commands or ["true"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pki.key_permissions failed")


class PkiCertExpiryAssertPlugin(BasePlugin):
    name = "pki.cert_expiry_assert"
    description = "Assert that a certificate remains valid for at least min_days."
    required_params = ("path",)
    optional_params = ("min_days", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "pki.cert_expiry_assert is a read-only certificate assertion with no file diff"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        seconds = int(params.get("min_days", 30)) * 86400
        return [f"openssl x509 -checkend {seconds} -noout -in {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="certificate expiry assertion failed")
        return PluginResult.success(stdout=out, stderr=err, data={"path": params["path"], "min_days": int(params.get("min_days", 30))})
