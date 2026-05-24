# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote package manager plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


_ALLOWED_MANAGERS = {"auto", "apt", "apt-get", "dnf", "yum", "zypper", "pacman"}


def _as_packages(params: Dict[str, Any]) -> list[str]:
    raw = params.get("packages", params.get("name"))
    if raw is None:
        raise PluginValidationError("package plugin requires name or packages")
    values = raw if isinstance(raw, list) else [raw]
    packages = [str(item).strip() for item in values if str(item).strip()]
    if not packages:
        raise PluginValidationError("package list must not be empty")
    return packages


def _manager(params: Dict[str, Any]) -> str:
    manager = str(params.get("manager", "auto"))
    if manager not in _ALLOWED_MANAGERS:
        raise PluginValidationError(
            "package manager must be auto, apt, apt-get, dnf, yum, zypper or pacman"
        )
    return manager


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _shell_header(params: Dict[str, Any]) -> str:
    manager = _manager(params)
    sudo = _sudo(params)
    return f"""
manager={quote(manager)}
if [ "$manager" = auto ]; then
  if command -v apt-get >/dev/null 2>&1; then manager=apt-get;
  elif command -v dnf >/dev/null 2>&1; then manager=dnf;
  elif command -v yum >/dev/null 2>&1; then manager=yum;
  elif command -v zypper >/dev/null 2>&1; then manager=zypper;
  elif command -v pacman >/dev/null 2>&1; then manager=pacman;
  else echo 'no supported package manager found' >&2; exit 2; fi
fi
is_installed() {{
  case "$manager" in
    apt|apt-get) dpkg-query -W -f='${{Status}}' "$1" 2>/dev/null | grep -q 'install ok installed' ;;
    dnf|yum|zypper) rpm -q "$1" >/dev/null 2>&1 ;;
    pacman) pacman -Qi "$1" >/dev/null 2>&1 ;;
    *) echo "unsupported package manager: $manager" >&2; exit 2 ;;
  esac
}}
run_install() {{
  case "$manager" in
    apt|apt-get) {sudo}env DEBIAN_FRONTEND=noninteractive apt-get install -y "$@" ;;
    dnf) {sudo}dnf install -y "$@" ;;
    yum) {sudo}yum install -y "$@" ;;
    zypper) {sudo}zypper --non-interactive install "$@" ;;
    pacman) {sudo}pacman -S --noconfirm "$@" ;;
  esac
}}
run_remove() {{
  case "$manager" in
    apt|apt-get) {sudo}env DEBIAN_FRONTEND=noninteractive apt-get remove -y "$@" ;;
    dnf) {sudo}dnf remove -y "$@" ;;
    yum) {sudo}yum remove -y "$@" ;;
    zypper) {sudo}zypper --non-interactive remove "$@" ;;
    pacman) {sudo}pacman -R --noconfirm "$@" ;;
  esac
}}
run_update_cache() {{
  case "$manager" in
    apt|apt-get) {sudo}apt-get update ;;
    dnf) {sudo}dnf makecache ;;
    yum) {sudo}yum makecache ;;
    zypper) {sudo}zypper --non-interactive refresh ;;
    pacman) {sudo}pacman -Sy --noconfirm ;;
  esac
}}
run_upgrade() {{
  case "$manager" in
    apt|apt-get) {sudo}env DEBIAN_FRONTEND=noninteractive apt-get upgrade -y ;;
    dnf) {sudo}dnf upgrade -y ;;
    yum) {sudo}yum update -y ;;
    zypper) {sudo}zypper --non-interactive update ;;
    pacman) {sudo}pacman -Syu --noconfirm ;;
  esac
}}
"""


def _package_args(packages: list[str]) -> str:
    return " ".join(quote(package) for package in packages)


class _PackagePlugin(BasePlugin):
    optional_params = ("name", "packages", "manager", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        _manager(params)
        if self.name in {"pkg.install", "pkg.remove", "pkg.query"}:
            _as_packages(params)

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(changed=False, message=f"dry-run: {self.name}", data={"params": params})


class PackageInstallPlugin(_PackagePlugin):
    """Install packages only when missing."""

    name = "pkg.install"
    description = "Install packages on a remote target."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        packages = _as_packages(params)
        package_args = _package_args(packages)
        command = _shell_header(params) + f"""
missing=""
for package in {package_args}; do
  if ! is_installed "$package"; then missing="$missing $package"; fi
done
if [ -n "$missing" ]; then
  # shellcheck disable=SC2086
  run_install $missing && echo {CHANGE_MARKER}
fi
"""
        rc, out, err = exec_remote(context, command, get_pty=bool(params.get("sudo", True)))
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.install failed", data={"packages": packages})


class PackageRemovePlugin(_PackagePlugin):
    """Remove packages only when installed."""

    name = "pkg.remove"
    description = "Remove packages from a remote target."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        packages = _as_packages(params)
        package_args = _package_args(packages)
        command = _shell_header(params) + f"""
present=""
for package in {package_args}; do
  if is_installed "$package"; then present="$present $package"; fi
done
if [ -n "$present" ]; then
  # shellcheck disable=SC2086
  run_remove $present && echo {CHANGE_MARKER}
fi
"""
        rc, out, err = exec_remote(context, command, get_pty=bool(params.get("sudo", True)))
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.remove failed", data={"packages": packages})


class PackageUpdateCachePlugin(_PackagePlugin):
    """Refresh the package manager cache."""

    name = "pkg.update_cache"
    description = "Refresh package manager metadata."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(
            context,
            _shell_header(params) + f"run_update_cache && echo {CHANGE_MARKER}\n",
            get_pty=bool(params.get("sudo", True)),
        )
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.update_cache failed")


class PackageUpgradePlugin(_PackagePlugin):
    """Upgrade installed packages through the selected package manager."""

    name = "pkg.upgrade"
    description = "Upgrade remote packages."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(
            context,
            _shell_header(params) + f"run_upgrade && echo {CHANGE_MARKER}\n",
            get_pty=bool(params.get("sudo", True)),
        )
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.upgrade failed")


class PackageQueryPlugin(_PackagePlugin):
    """Query package installation state without changing the target."""

    name = "pkg.query"
    description = "Query package installation state."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        packages = _as_packages(params)
        package_args = _package_args(packages)
        command = _shell_header(params) + f"""
for package in {package_args}; do
  if is_installed "$package"; then echo "$package installed"; else echo "$package missing"; fi
done
"""
        rc, out, err = exec_remote(context, command)
        states = {}
        for line in out.splitlines():
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                states[parts[0]] = parts[1]
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pkg.query failed")
        return PluginResult.success(changed=False, stdout=out, data={"packages": states})


def _inspection_header(params: Dict[str, Any]) -> str:
    manager = _manager(params)
    return f"""
manager={quote(manager)}
if [ "$manager" = auto ]; then
  if command -v apt-get >/dev/null 2>&1; then manager=apt-get;
  elif command -v dnf >/dev/null 2>&1; then manager=dnf;
  elif command -v yum >/dev/null 2>&1; then manager=yum;
  elif command -v zypper >/dev/null 2>&1; then manager=zypper;
  elif command -v pacman >/dev/null 2>&1; then manager=pacman;
  else echo 'no supported package manager found' >&2; exit 2; fi
fi
"""


class PackageVersionAssertPlugin(_PackagePlugin):
    name = "pkg.version_assert"
    description = "Assert that an installed package version matches the expected version."
    required_params = ("name", "version")
    optional_params = ("manager", "sudo")
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        name = quote(params["name"])
        version = quote(params["version"])
        command = _inspection_header(params) + f"""
case "$manager" in
  apt|apt-get) installed=$(dpkg-query -W -f='${{Version}}' {name} 2>/dev/null) ;;
  dnf|yum|zypper) installed=$(rpm -q --qf '%{{VERSION}}-%{{RELEASE}}' {name}) ;;
  pacman) installed=$(pacman -Q {name} | awk '{{print $2}}') ;;
  *) echo "unsupported package manager: $manager" >&2; exit 2 ;;
esac
test "$installed" = {version}
"""
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pkg.version_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"name": params["name"], "version": params["version"]})


class PackageOwnerPlugin(_PackagePlugin):
    name = "pkg.owner"
    description = "Report which package owns a file path."
    required_params = ("path",)
    optional_params = ("manager", "sudo")
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = quote(params["path"])
        command = _inspection_header(params) + f"""
case "$manager" in
  apt|apt-get) dpkg-query -S {path} ;;
  dnf|yum|zypper) rpm -qf {path} ;;
  pacman) pacman -Qo {path} ;;
  *) echo "unsupported package manager: $manager" >&2; exit 2 ;;
esac
"""
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pkg.owner failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"owner": out.strip()})


class PackageFilesPlugin(_PackagePlugin):
    name = "pkg.files"
    description = "List files installed by a package."
    required_params = ("name",)
    optional_params = ("manager", "sudo")
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        name = quote(params["name"])
        command = _inspection_header(params) + f"""
case "$manager" in
  apt|apt-get) dpkg -L {name} ;;
  dnf|yum|zypper) rpm -ql {name} ;;
  pacman) pacman -Ql {name} ;;
  *) echo "unsupported package manager: $manager" >&2; exit 2 ;;
esac
"""
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pkg.files failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"files": out.splitlines()})


class PackageVerifyPlugin(_PackagePlugin):
    name = "pkg.verify"
    description = "Verify installed package file integrity when the package manager supports it."
    optional_params = ("name", "packages", "manager", "sudo")
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        packages = _package_args(_as_packages(params))
        sudo = _sudo(params)
        command = _inspection_header(params) + f"""
case "$manager" in
  apt|apt-get) if command -v debsums >/dev/null 2>&1; then {sudo}debsums -s {packages}; else {sudo}dpkg -V {packages}; fi ;;
  dnf|yum|zypper) {sudo}rpm -V {packages} ;;
  pacman) {sudo}pacman -Qk {packages} ;;
  *) echo "unsupported package manager: $manager" >&2; exit 2 ;;
esac
"""
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pkg.verify failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class PackageCleanPlugin(_PackagePlugin):
    name = "pkg.clean"
    description = "Clean package-manager caches."
    optional_params = ("manager", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        command = _inspection_header(params) + f"""
case "$manager" in
  apt|apt-get) {sudo}apt-get clean ;;
  dnf) {sudo}dnf clean all ;;
  yum) {sudo}yum clean all ;;
  zypper) {sudo}zypper clean --all ;;
  pacman) {sudo}pacman -Sc --noconfirm ;;
  *) echo "unsupported package manager: $manager" >&2; exit 2 ;;
esac
"""
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}", get_pty=bool(params.get("sudo", True)))
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.clean failed")
