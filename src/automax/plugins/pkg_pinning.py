# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Package lock, version pin and repository priority plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _manager(params: Dict[str, Any]) -> str:
    return str(params.get("manager", "auto"))


def _packages(params: Dict[str, Any]) -> list[str]:
    raw = params.get("packages") or params.get("name")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    raise PluginValidationError("package operation requires name or packages")


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


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
        if manager == "apt":
            return [f"{sudo}apt-mark hold {packages}"]
        if manager in {"dnf", "yum"}:
            return [f"{sudo}{manager} versionlock add {packages}"]
        if manager == "zypper":
            return [f"{sudo}zypper addlock {packages}"]
        return [f"if command -v apt-mark >/dev/null 2>&1; then {sudo}apt-mark hold {packages}; elif command -v dnf >/dev/null 2>&1; then {sudo}dnf versionlock add {packages}; elif command -v yum >/dev/null 2>&1; then {sudo}yum versionlock add {packages}; elif command -v zypper >/dev/null 2>&1; then {sudo}zypper addlock {packages}; else echo 'no supported package lock manager found' >&2; exit 1; fi"]

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
        if manager == "apt":
            return [f"{sudo}apt-mark unhold {packages}"]
        if manager in {"dnf", "yum"}:
            return [f"{sudo}{manager} versionlock delete {packages}"]
        if manager == "zypper":
            return [f"{sudo}zypper removelock {packages}"]
        return [f"if command -v apt-mark >/dev/null 2>&1; then {sudo}apt-mark unhold {packages}; elif command -v dnf >/dev/null 2>&1; then {sudo}dnf versionlock delete {packages}; elif command -v yum >/dev/null 2>&1; then {sudo}yum versionlock delete {packages}; elif command -v zypper >/dev/null 2>&1; then {sudo}zypper removelock {packages}; else echo 'no supported package lock manager found' >&2; exit 1; fi"]


class PkgVersionPinPlugin(BasePlugin):
    name = "pkg.version_pin"
    description = "Create an explicit package version pin/preference file."
    required_params = ("name", "version")
    optional_params = ("manager", "priority", "file", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        if params.get("file"):
            return str(params["file"])
        return f"/etc/apt/preferences.d/automax-{params['name']}"

    def _content(self, params: Dict[str, Any]) -> str:
        manager = _manager(params)
        if manager not in {"auto", "apt"}:
            return f"# Managed by automax\n# {manager} version pin: {params['name']} {params['version']}\n"
        priority = int(params.get("priority", 1001))
        return f"Package: {params['name']}\nPin: version {params['version']}\nPin-Priority: {priority}\n"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(self._path(params), self._content(params), "package-pin-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = self._path(params)
        content = self._content(params)
        sudo = _sudo(params)
        temp = "/tmp/automax-pkg-pin.$$"
        commands = [f"cat > {temp} <<'EOF'\n{content}EOF"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pkg.version_pin failed")


class PkgRepoPriorityPlugin(BasePlugin):
    name = "pkg.repo_priority"
    description = "Install package repository priority or pinning configuration."
    required_params = ("name", "priority")
    optional_params = ("manager", "file", "content", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        if params.get("file"):
            return str(params["file"])
        manager = _manager(params)
        if manager in {"dnf", "yum"}:
            return f"/etc/yum.repos.d/{params['name']}.repo"
        return f"/etc/apt/preferences.d/{params['name']}-priority"

    def _content(self, params: Dict[str, Any]) -> str:
        if params.get("content"):
            return str(params["content"])
        return f"Package: *\nPin: release o={params['name']}\nPin-Priority: {params['priority']}\n"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(self._path(params), self._content(params), "repo-priority-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = self._path(params)
        content = self._content(params)
        sudo = _sudo(params)
        temp = "/tmp/automax-repo-priority.$$"
        commands = [f"cat > {temp} <<'EOF'\n{content}EOF"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="pkg.repo_priority failed")
