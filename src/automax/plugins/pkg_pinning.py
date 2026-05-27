# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Package lock, version pin and repository priority plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_file, quote, result_from_remote, sudo_prefix


def _sudo(params: Dict[str, Any]) -> str:
    return sudo_prefix(params, default=True)


def _manager(params: Dict[str, Any]) -> str:
    manager = str(params.get("manager", "auto"))
    if manager not in {"auto", "apt", "dnf", "yum", "zypper"}:
        raise PluginValidationError("manager must be auto, apt, dnf, yum or zypper")
    return manager


def _packages(params: Dict[str, Any]) -> list[str]:
    raw = params.get("packages") or params.get("name")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    raise PluginValidationError("package operation requires name or packages")


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


def _auto_manager_script(commands: Dict[str, str]) -> str:
    checks = []
    if "apt" in commands:
        checks.append(f"if command -v apt-mark >/dev/null 2>&1; then {commands['apt']};")
    if "dnf" in commands:
        checks.append(f"elif command -v dnf >/dev/null 2>&1; then {commands['dnf']};")
    if "yum" in commands:
        checks.append(f"elif command -v yum >/dev/null 2>&1; then {commands['yum']};")
    if "zypper" in commands:
        checks.append(f"elif command -v zypper >/dev/null 2>&1; then {commands['zypper']};")
    checks.append("else echo 'no supported package manager found' >&2; exit 1; fi")
    script = " ".join(checks)
    return script.replace("if elif", "if")


class PkgHoldPlugin(BasePlugin):
    name = "pkg.hold"
    description = "Hold or lock package versions with the native package manager."
    required_params: tuple[str, ...] = ()
    optional_params = ("name", "packages", "manager", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _diff("package-locks", "\n".join(_packages(params)) + "\n", "package-lock-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        packages = " ".join(quote(item) for item in _packages(params))
        manager = _manager(params)
        sudo = _sudo(params)
        commands = {
            "apt": f"{sudo}apt-mark hold {packages}",
            "dnf": f"command -v dnf >/dev/null 2>&1 && {sudo}dnf versionlock add {packages}",
            "yum": f"command -v yum >/dev/null 2>&1 && {sudo}yum versionlock add {packages}",
            "zypper": f"{sudo}zypper addlock {packages}",
        }
        if manager == "auto":
            return [_auto_manager_script(commands)]
        return [commands[manager]]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pkg.hold failed")


class PkgUnholdPlugin(PkgHoldPlugin):
    name = "pkg.unhold"
    description = "Remove package holds or version locks."

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        packages = " ".join(quote(item) for item in _packages(params))
        manager = _manager(params)
        sudo = _sudo(params)
        commands = {
            "apt": f"{sudo}apt-mark unhold {packages}",
            "dnf": f"command -v dnf >/dev/null 2>&1 && {sudo}dnf versionlock delete {packages}",
            "yum": f"command -v yum >/dev/null 2>&1 && {sudo}yum versionlock delete {packages}",
            "zypper": f"{sudo}zypper removelock {packages}",
        }
        if manager == "auto":
            return [_auto_manager_script(commands)]
        return [commands[manager]]


class PkgVersionPinPlugin(BasePlugin):
    name = "pkg.version_pin"
    description = "Pin a package version using the native package-manager mechanism."
    required_params = ("name", "version")
    optional_params = ("manager", "priority", "file", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _apt_path(self, params: Dict[str, Any]) -> str:
        if params.get("file"):
            return str(params["file"])
        return f"/etc/apt/preferences.d/automax-{params['name']}"

    def _apt_content(self, params: Dict[str, Any]) -> str:
        priority = int(params.get("priority", 1001))
        return f"Package: {params['name']}\nPin: version {params['version']}\nPin-Priority: {priority}\n"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        manager = _manager(params)
        if manager in {"auto", "apt"}:
            return _diff(self._apt_path(params), self._apt_content(params), "package-pin-plan")
        return _diff("package-versionlock", f"{manager}: {params['name']}-{params['version']}\n", "package-pin-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        manager = _manager(params)
        sudo = _sudo(params)
        name = str(params["name"])
        version = str(params["version"])
        lock_spec = quote(f"{name}-{version}")
        zypper_spec = quote(f"{name}={version}")
        apt_path = self._apt_path(params)
        apt_content = self._apt_content(params)
        temp = "/tmp/automax-pkg-pin.$$"
        apt_commands = [heredoc_to_file(temp, apt_content)]
        if bool(params.get("backup", True)):
            apt_commands.append(f"test ! -e {quote(apt_path)} || {sudo}cp -p {quote(apt_path)} {quote(apt_path + str(params.get('backup_suffix', '.bak')))}")
        apt_commands.extend([f"{sudo}install -m 0644 {temp} {quote(apt_path)}", f"rm -f {temp}"])
        commands = {
            "apt": " && ".join(apt_commands),
            "dnf": f"command -v dnf >/dev/null 2>&1 && {sudo}dnf versionlock add {lock_spec}",
            "yum": f"command -v yum >/dev/null 2>&1 && {sudo}yum versionlock add {lock_spec}",
            "zypper": f"{sudo}zypper addlock {zypper_spec}",
        }
        if manager == "auto":
            return [_auto_manager_script(commands)]
        return [commands[manager]]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pkg.version_pin failed")


class PkgRepoPriorityPlugin(BasePlugin):
    name = "pkg.repo_priority"
    description = "Install package repository priority or pinning configuration for apt, dnf/yum or zypper."
    required_params = ("name", "priority")
    optional_params = ("manager", "file", "content", "baseurl", "enabled", "gpgcheck", "gpgkey", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        if params.get("file"):
            return str(params["file"])
        manager = _manager(params)
        if manager in {"dnf", "yum"}:
            return f"/etc/yum.repos.d/{params['name']}.repo"
        if manager == "zypper":
            return f"/etc/zypp/repos.d/{params['name']}.repo"
        return f"/etc/apt/preferences.d/{params['name']}-priority"

    def _content(self, params: Dict[str, Any]) -> str:
        if params.get("content"):
            return str(params["content"])
        manager = _manager(params)
        if manager in {"auto", "apt"}:
            return f"Package: *\nPin: release o={params['name']}\nPin-Priority: {params['priority']}\n"
        if manager in {"dnf", "yum", "zypper"}:
            if not params.get("baseurl"):
                raise PluginValidationError(f"pkg.repo_priority with manager={manager} requires content or baseurl")
            enabled = int(bool(params.get("enabled", True)))
            gpgcheck = int(bool(params.get("gpgcheck", True)))
            lines = [
                f"[{params['name']}]\n",
                f"name={params['name']}\n",
                f"baseurl={params['baseurl']}\n",
                f"enabled={enabled}\n",
                f"gpgcheck={gpgcheck}\n",
                f"priority={params['priority']}\n",
            ]
            if params.get("gpgkey"):
                lines.append(f"gpgkey={params['gpgkey']}\n")
            return "".join(lines)
        raise PluginValidationError("unsupported package manager")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(self._path(params), self._content(params), "repo-priority-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = self._path(params)
        content = self._content(params)
        sudo = _sudo(params)
        temp = "/tmp/automax-repo-priority.$$"
        commands = [heredoc_to_file(temp, content)]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pkg.repo_priority failed")
