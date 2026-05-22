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
