# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""User, session and authentication hardening plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError, RenderedFileInstallMixin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



def _settings_content(settings: Dict[str, Any], sep: str = " ") -> str:
    return "".join(f"{key}{sep}{value}\n" for key, value in sorted(settings.items()))


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class SshdConfigPlugin(RenderedFileInstallMixin, BasePlugin):
    name = "security.sshd.config"
    description = "Install an sshd_config.d hardening drop-in with sshd syntax validation."
    required_params = ("name", "settings")
    optional_params = ("path", "backup", "backup_suffix", "reload", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "sshd"
    rendered_file_diff_kind = "sshd-config-plan"

    def _path(self, params: Dict[str, Any]) -> str:
        name = str(params["name"])
        if not name.endswith(".conf"):
            name += ".conf"
        return str(params.get("path", f"/etc/ssh/sshd_config.d/{name}"))

    def _content(self, params: Dict[str, Any]) -> str:
        settings = params.get("settings")
        if not isinstance(settings, dict) or not settings:
            raise PluginValidationError("security.sshd.config settings must be a non-empty mapping")
        return "# Managed by automax\n" + _settings_content(settings)

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._content(params)

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = self.rendered_file_sudo(params)
        commands = [f"{sudo}sshd -t"]
        if bool(params.get("reload", True)):
            commands.append(f"{sudo}systemctl reload sshd || {sudo}systemctl reload ssh")
        return commands

class LoginDefsPlugin(BasePlugin):
    name = "login.defs"
    description = "Manage /etc/login.defs settings with backup."
    required_params = ("settings",)
    optional_params = ("path", "backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "pwquality"
    rendered_file_diff_kind = "password-policy-plan"

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", "/etc/login.defs"))

    def _content(self, params: Dict[str, Any]) -> str:
        settings = params.get("settings")
        if not isinstance(settings, dict) or not settings:
            raise PluginValidationError("login.defs settings must be a non-empty mapping")
        return _settings_content(settings)

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _diff(self._path(params), self._content(params), "login-defs-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = self._path(params)
        sudo = sudo_prefix(params, default=True)
        script_lines = []
        for key, value in sorted(params["settings"].items()):
            script_lines.append(f"if grep -Eq '^[#[:space:]]*{key}[[:space:]]+' {quote(path)}; then {sudo}sed -i -E 's|^[#[:space:]]*{key}[[:space:]]+.*|{key} {value}|' {quote(path)}; else printf '%s\\n' {quote(f'{key} {value}')} | {sudo}tee -a {quote(path)} >/dev/null; fi")
        commands = []
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.extend(script_lines)
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="login.defs failed")

class PasswordPolicyPlugin(RenderedFileInstallMixin, BasePlugin):
    name = "security.password.policy"
    description = "Install a pwquality password policy drop-in."
    required_params = ("name", "settings")
    optional_params = ("path", "backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "pwquality"
    rendered_file_diff_kind = "password-policy-plan"

    def _path(self, params: Dict[str, Any]) -> str:
        name = str(params["name"])
        if not name.endswith(".conf"):
            name += ".conf"
        return str(params.get("path", f"/etc/security/pwquality.conf.d/{name}"))

    def _content(self, params: Dict[str, Any]) -> str:
        settings = params.get("settings")
        if not isinstance(settings, dict) or not settings:
            raise PluginValidationError("security.password.policy settings must be a non-empty mapping")
        return "# Managed by automax\n" + _settings_content(settings, " = ")

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._content(params)

class AuthselectProfilePlugin(BasePlugin):
    name = "security.authselect.profile"
    description = "Select an authselect profile with optional features and backup."
    required_params = ("profile",)
    optional_params = ("features", "backup", "force", "sudo")
    opens_remote_session = True

    def _features(self, params: Dict[str, Any]) -> list[str]:
        raw = params.get("features") or []
        if isinstance(raw, str):
            return [raw]
        return [str(item) for item in raw]

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.authselect.profile changes PAM/NSS profile state through authselect"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
        features = " ".join(quote(item) for item in self._features(params))
        backup = " --backup=automax" if bool(params.get("backup", True)) else ""
        force = " --force" if bool(params.get("force", False)) else ""
        return [f"{sudo}authselect select {quote(params['profile'])}{(' ' + features) if features else ''}{backup}{force}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.authselect.profile failed")

# Extended sshd_config rendering with Match blocks and explicit validation controls.

def _sshd_content_extended(self: SshdConfigPlugin, params: Dict[str, Any]) -> str:
    content = SshdConfigPlugin._content(self, params)
    blocks = params.get("match_blocks") or []
    for block in blocks:
        if not isinstance(block, dict) or "match" not in block or "settings" not in block:
            raise PluginValidationError("security.sshd.config match_blocks entries require match and settings")
        content += f"\nMatch {block['match']}\n"
        settings = block["settings"]
        if not isinstance(settings, dict):
            raise PluginValidationError("security.sshd.config match block settings must be a mapping")
        for key, value in sorted(settings.items()):
            content += f"    {key} {value}\n"
    return content

class ExtendedSshdConfigPlugin(SshdConfigPlugin):
    """security.sshd.config with Match block and validation controls."""

    optional_params = ("path", "backup", "backup_suffix", "reload", "validate_before_reload", "match_blocks", "sudo")

    def _content(self, params: Dict[str, Any]) -> str:
        return _sshd_content_extended(self, params)

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if not bool(params.get("validate_before_reload", True)):
            commands: list[str] = []
        else:
            commands = [f"{self.rendered_file_sudo(params)}sshd -t"]
        if bool(params.get("reload", True)):
            sudo = self.rendered_file_sudo(params)
            commands.append(f"{sudo}systemctl reload sshd || {sudo}systemctl reload ssh")
        return commands
