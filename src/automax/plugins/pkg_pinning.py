# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Package lock, version pin and repository priority plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import cleanup_trap_command, CHANGE_MARKER, exec_remote, predicate_result_from_remote, heredoc_to_file_expr, shell_var_ref, tempfile_command, quote, result_from_remote, sudo_prefix



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
    name = "os.package.hold.add"
    description = "Hold or lock package versions with the native package manager."
    required_params: tuple[str, ...] = ()
    optional_params = ("name", "packages", "manager", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _diff("package-locks", "\n".join(_packages(params)) + "\n", "package-lock-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        packages = " ".join(quote(item) for item in _packages(params))
        manager = _manager(params)
        sudo = sudo_prefix(params, default=True)
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
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="os.package.hold.add failed")


class PkgUnholdPlugin(PkgHoldPlugin):
    name = "os.package.hold.remove"
    description = "Remove package holds or version locks."

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        packages = " ".join(quote(item) for item in _packages(params))
        manager = _manager(params)
        sudo = sudo_prefix(params, default=True)
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
    name = "os.package.version.pin"
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
        sudo = sudo_prefix(params, default=True)
        name = str(params["name"])
        version = str(params["version"])
        lock_spec = quote(f"{name}-{version}")
        zypper_spec = quote(f"{name}={version}")
        apt_path = self._apt_path(params)
        apt_content = self._apt_content(params)
        temp_var = "automax_pkg_pin_tmp"
        temp = shell_var_ref(temp_var)
        apt_commands = [tempfile_command(temp_var, "pkg-pin"), cleanup_trap_command(temp_var), heredoc_to_file_expr(temp, apt_content)]
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
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="os.package.version.pin failed")


class PkgRepoPriorityPlugin(BasePlugin):
    name = "os.package.repo.priority.set"
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
                raise PluginValidationError(f"os.package.repo.priority.set with manager={manager} requires content or baseurl")
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
        sudo = sudo_prefix(params, default=True)
        temp_var = "automax_repo_priority_tmp"
        temp = shell_var_ref(temp_var)
        commands = [tempfile_command(temp_var, "repo-priority"), cleanup_trap_command(temp_var), heredoc_to_file_expr(temp, content)]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"{sudo}install -m 0644 {temp} {quote(path)}")
        commands.append(f"rm -f {temp}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="os.package.repo.priority.set failed")


class PkgHoldListPlugin(BasePlugin):
    name = "os.package.hold.list"
    description = "List packages currently held by the package manager."
    optional_params = ("manager", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        manager = _manager(params)
        if manager in {"auto", "apt", "apt-get"}:
            return ["apt-mark showhold"]
        return ["echo 'hold listing is only supported for apt-based systems' >&2; exit 2"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        packages = [line.strip() for line in out.splitlines() if line.strip()] if rc == 0 else []
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.hold.list failed", data={"packages": packages})


class PkgHoldCheckPlugin(PkgHoldListPlugin):
    name = "os.package.hold.check"
    description = "Check package hold state."
    required_params = ("name",)
    optional_params = ("manager", "state", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        manager = _manager(params)
        if manager not in {"auto", "apt", "apt-get"}:
            return ["echo 'hold checks are only supported for apt-based systems' >&2; exit 2"]
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("os.package.hold.check state must be present or absent")
        grep = f"apt-mark showhold | grep -Fx -- {quote(params['name'])} >/dev/null"
        return [grep if state == "present" else f"! {grep}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.package.hold.check failed",
            data_key="matches",
            data={"name": str(params["name"]), "state": str(params.get("state", "present"))},
        )


class PkgRepoPriorityCheckPlugin(PkgRepoPriorityPlugin):
    name = "os.package.repo.priority.check"
    description = "Check whether a package repository priority drop-in exists with expected content."
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = self._path(params)
        content = self._content(params)
        escaped = content.replace("'", "'\\''")
        return [f"test -e {quote(path)} && diff -u {quote(path)} - <<'EOF'\n{escaped}EOF"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.package.repo.priority.check failed",
            data_key="matches",
            data={"path": self._path(params)},
        )
