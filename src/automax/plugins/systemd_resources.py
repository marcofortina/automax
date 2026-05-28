# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Systemd unit, timer, tmpfiles and sysusers plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext
from automax.plugins.base import BasePlugin, PluginValidationError, RenderedFileInstallMixin
from automax.plugins.remote_utils import cleanup_trap_command, heredoc_to_file_expr, shell_var_ref, tempfile_command, quote, sudo_prefix



def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


def _install_cmd(path: str, content: str, mode: str, params: Dict[str, Any]) -> str:
    sudo = sudo_prefix(params, default=True)
    temp_var = "automax_systemd_tmp"
    temp = shell_var_ref(temp_var)
    commands = [tempfile_command(temp_var, "systemd"), cleanup_trap_command(temp_var), heredoc_to_file_expr(temp, content)]
    if bool(params.get("backup", True)):
        commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
    commands.append(f"{sudo}install -D -m {mode} {temp} {quote(path)}")
    commands.append(f"rm -f {temp}")
    return " && ".join(commands)


def _content(params: Dict[str, Any]) -> str:
    if params.get("content") is None:
        raise PluginValidationError("systemd resource plugins require content")
    return str(params["content"])


class SystemdUnitPlugin(RenderedFileInstallMixin, BasePlugin):
    name = "systemd.unit"
    description = "Install a systemd unit file with backup, daemon-reload and optional enable/start."
    required_params = ("name", "content")
    optional_params = ("path", "enable", "start", "backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "systemd"
    rendered_file_diff_kind = "systemd-unit-plan"

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", f"/etc/systemd/system/{params['name']}"))

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return _content(params)

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = self.rendered_file_sudo(params)
        commands = [f"{sudo}systemctl daemon-reload"]
        if bool(params.get("enable", False)):
            commands.append(f"{sudo}systemctl enable {quote(params['name'])}")
        if bool(params.get("start", False)):
            commands.append(f"{sudo}systemctl start {quote(params['name'])}")
        return commands


class SystemdTimerPlugin(SystemdUnitPlugin):
    name = "systemd.timer"
    description = "Install a systemd timer file with backup, daemon-reload and optional enable/start."

    def _path(self, params: Dict[str, Any]) -> str:
        name = str(params["name"])
        if not name.endswith(".timer"):
            name += ".timer"
        return str(params.get("path", f"/etc/systemd/system/{name}"))


class SystemdTmpfilesPlugin(RenderedFileInstallMixin, BasePlugin):
    name = "systemd.tmpfiles"
    description = "Install a tmpfiles.d drop-in and optionally apply it immediately."
    required_params = ("name", "content")
    optional_params = ("path", "apply", "backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "systemd"
    rendered_file_diff_kind = "systemd-unit-plan"

    def _path(self, params: Dict[str, Any]) -> str:
        name = str(params["name"])
        if not name.endswith(".conf"):
            name += ".conf"
        return str(params.get("path", f"/etc/tmpfiles.d/{name}"))

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return _content(params)

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if bool(params.get("apply", False)):
            return [f"{self.rendered_file_sudo(params)}systemd-tmpfiles --create {quote(self._path(params))}"]
        return []


class SystemdSysusersPlugin(SystemdTmpfilesPlugin):
    name = "systemd.sysusers"
    description = "Install a sysusers.d drop-in and optionally apply it immediately."

    def _path(self, params: Dict[str, Any]) -> str:
        name = str(params["name"])
        if not name.endswith(".conf"):
            name += ".conf"
        return str(params.get("path", f"/etc/sysusers.d/{name}"))

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if bool(params.get("apply", False)):
            return [f"{self.rendered_file_sudo(params)}systemd-sysusers {quote(self._path(params))}"]
        return []
