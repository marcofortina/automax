# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote package manager plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix


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



def _shell_header(params: Dict[str, Any]) -> str:
    manager = _manager(params)
    sudo = sudo_prefix(params, default=True)
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
        if self.name in {"os.package.install", "os.package.remove", "os.package.query", "os.package.check"}:
            _as_packages(params)

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(changed=False, message=f"dry-run: {self.name}", data={"params": params})


class PackageInstallPlugin(_PackagePlugin):
    """Install packages only when missing."""

    name = "os.package.install"
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
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.install failed", data={"packages": packages})


class PackageRemovePlugin(_PackagePlugin):
    """Remove packages only when installed."""

    name = "os.package.remove"
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
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.remove failed", data={"packages": packages})


class PackageUpdateCachePlugin(_PackagePlugin):
    """Refresh the package manager cache."""

    name = "os.package.update_cache"
    description = "Refresh package manager metadata."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(
            context,
            _shell_header(params) + f"run_update_cache && echo {CHANGE_MARKER}\n",
            get_pty=bool(params.get("sudo", True)),
        )
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.update_cache failed")


class PackageUpgradePlugin(_PackagePlugin):
    """Upgrade installed packages through the selected package manager."""

    name = "os.package.upgrade"
    description = "Upgrade remote packages."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(
            context,
            _shell_header(params) + f"run_upgrade && echo {CHANGE_MARKER}\n",
            get_pty=bool(params.get("sudo", True)),
        )
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.upgrade failed")


class PackageQueryPlugin(_PackagePlugin):
    """Query package installation state without changing the target."""

    name = "os.package.query"
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
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.package.query failed")
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
    name = "os.package.version.check"
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
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.package.version.check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"name": params["name"], "version": params["version"]})


class PackageOwnerPlugin(_PackagePlugin):
    name = "os.package.owner"
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
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.package.owner failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"owner": out.strip()})


class PackageFilesPlugin(_PackagePlugin):
    name = "os.package.files"
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
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.package.files failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"files": out.splitlines()})


class PackageVerifyPlugin(_PackagePlugin):
    name = "os.package.verify"
    description = "Verify installed package file integrity when the package manager supports it."
    optional_params = ("name", "packages", "manager", "sudo")
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        packages = _package_args(_as_packages(params))
        sudo = sudo_prefix(params, default=True)
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
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.package.verify failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class PackageCleanPlugin(_PackagePlugin):
    name = "os.package.clean"
    description = "Clean package-manager caches."
    optional_params = ("manager", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
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
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.clean failed")

# Extended package operation renderers expose safer enterprise controls.


def _repo_opts(params: Dict[str, Any]) -> str:
    opts: list[str] = []
    for repo in _as_list(params.get("enablerepo")):
        opts.append(f"--enablerepo={quote(repo)}")
    for repo in _as_list(params.get("disablerepo")):
        opts.append(f"--disablerepo={quote(repo)}")
    return " ".join(opts)


def _pkg_install_manual(self: PackageInstallPlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    self.validate(params)
    packages = _as_packages(params)
    if params.get("version") and len(packages) != 1:
        raise PluginValidationError("os.package.install version requires exactly one package")
    package_exprs = [f"{packages[0]}={params['version']}" if params.get("version") else package for package in packages]
    pkg_args = _package_args(package_exprs)
    sudo = sudo_prefix(params, default=True)
    no_recommends = " --no-install-recommends" if bool(params.get("no_recommends", False)) else ""
    allow_downgrade = " --allow-downgrades" if bool(params.get("allow_downgrade", False)) else ""
    repo_opts = _repo_opts(params)
    command = _shell_header(params) + f"""
missing=""
for package in {_package_args(packages)}; do
  if ! is_installed "$package"; then missing="$missing $package"; fi
done
if [ -n "$missing" ]; then
  case "$manager" in
    apt|apt-get) {sudo}env DEBIAN_FRONTEND=noninteractive apt-get install -y{no_recommends}{allow_downgrade} {pkg_args} ;;
    dnf) {sudo}dnf install -y {repo_opts} {pkg_args} ;;
    yum) {sudo}yum install -y {repo_opts} {pkg_args} ;;
    zypper) {sudo}zypper --non-interactive install {pkg_args} ;;
    pacman) {sudo}pacman -S --noconfirm {pkg_args} ;;
  esac
  echo {CHANGE_MARKER}
fi
"""
    if bool(params.get("lock_after_install", False)):
        command += f"\nif command -v apt-mark >/dev/null 2>&1; then {sudo}apt-mark hold {_package_args(packages)}; elif command -v dnf >/dev/null 2>&1; then {sudo}dnf versionlock add {_package_args(packages)}; elif command -v yum >/dev/null 2>&1; then {sudo}yum versionlock add {_package_args(packages)}; elif command -v zypper >/dev/null 2>&1; then {sudo}zypper addlock {_package_args(packages)}; fi\n"
    return [command]


def _pkg_install_execute(self: PackageInstallPlugin, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
    rc, out, err = exec_remote(context, self.manual_commands(params, context)[0], get_pty=bool(params.get("sudo", True)))
    return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.install failed", data={"packages": _as_packages(params)})


def _pkg_remove_manual(self: PackageRemovePlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    self.validate(params)
    packages = _as_packages(params)
    protected = set(_as_list(params.get("protect_packages"))) | {"sudo", "systemd", "openssh-server", "ssh", "python3"}
    dangerous = bool(params.get("purge", False)) or bool(params.get("autoremove", False)) or bool(set(packages) & protected)
    if dangerous and not bool(params.get("confirm", False)):
        raise PluginValidationError("os.package.remove purge/autoremove/protected package removal requires confirm=true")
    pkg_args = _package_args(packages)
    sudo = sudo_prefix(params, default=True)
    purge = " purge" if bool(params.get("purge", False)) else " remove"
    autoremove = f" && {sudo}apt-get autoremove -y" if bool(params.get("autoremove", False)) else ""
    command = _shell_header(params) + f"""
present=""
for package in {pkg_args}; do
  if is_installed "$package"; then present="$present $package"; fi
done
if [ -n "$present" ]; then
  case "$manager" in
    apt|apt-get) {sudo}env DEBIAN_FRONTEND=noninteractive apt-get{purge} -y $present{autoremove} ;;
    dnf) {sudo}dnf remove -y $present ;;
    yum) {sudo}yum remove -y $present ;;
    zypper) {sudo}zypper --non-interactive remove $present ;;
    pacman) {sudo}pacman -R --noconfirm $present ;;
  esac
  echo {CHANGE_MARKER}
fi
"""
    return [command]


def _pkg_remove_execute(self: PackageRemovePlugin, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
    rc, out, err = exec_remote(context, self.manual_commands(params, context)[0], get_pty=bool(params.get("sudo", True)))
    return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.remove failed", data={"packages": _as_packages(params)})


def _pkg_upgrade_manual(self: PackageUpgradePlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    _manager(params)
    sudo = sudo_prefix(params, default=True)
    excludes = " ".join(f"--exclude={quote(item)}" for item in _as_list(params.get("exclude")))
    download = " --download-only" if bool(params.get("download_only", False)) else ""
    security = " --security" if bool(params.get("security_only", False)) else ""
    command = _shell_header(params) + f"""
case "$manager" in
  apt|apt-get) {sudo}env DEBIAN_FRONTEND=noninteractive apt-get upgrade -y{download} ;;
  dnf) {sudo}dnf upgrade -y{security}{download} {excludes} ;;
  yum) {sudo}yum update -y{security}{download} {excludes} ;;
  zypper) {sudo}zypper --non-interactive update ;;
  pacman) {sudo}pacman -Syu --noconfirm ;;
esac
echo {CHANGE_MARKER}
"""
    if bool(params.get("reboot_required_check", False)):
        command += "\nif command -v needs-restarting >/dev/null 2>&1; then needs-restarting -r || true; elif test -e /var/run/reboot-required; then cat /var/run/reboot-required; fi\n"
    return [command]


def _pkg_upgrade_execute(self: PackageUpgradePlugin, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
    rc, out, err = exec_remote(context, self.manual_commands(params, context)[0], get_pty=bool(params.get("sudo", True)))
    return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.upgrade failed")



class ExtendedPackageInstallPlugin(PackageInstallPlugin):
    """os.package.install with version, repository and package-lock controls."""

    optional_params = ("name", "packages", "manager", "version", "enablerepo", "disablerepo", "no_recommends", "lock_after_install", "allow_downgrade", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return _pkg_install_manual(self, params, context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return _pkg_install_execute(self, params, context)


class ExtendedPackageRemovePlugin(PackageRemovePlugin):
    """os.package.remove with purge, autoremove and protected-package controls."""

    optional_params = ("name", "packages", "manager", "purge", "autoremove", "confirm", "protect_packages", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return _pkg_remove_manual(self, params, context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return _pkg_remove_execute(self, params, context)


class ExtendedPackageUpgradePlugin(PackageUpgradePlugin):
    """os.package.upgrade with security, download-only and reboot-check controls."""

    optional_params = ("manager", "security_only", "exclude", "download_only", "reboot_required_check", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return _pkg_upgrade_manual(self, params, context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return _pkg_upgrade_execute(self, params, context)

# Helper intentionally appended after extended renderers; functions resolve globals at call time.
def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


class PackageCheckPlugin(_PackagePlugin):
    name = "os.package.check"
    description = "Assert package installation state and optionally version."
    required_params = ("name",)
    optional_params = ("packages", "manager", "state", "version", "sudo")
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        packages = _as_packages(params)
        state = str(params.get("state", "installed"))
        if state not in {"installed", "absent"}:
            raise PluginValidationError("os.package.check state must be installed or absent")
        package_args = _package_args(packages)
        version_check = ""
        if params.get("version") and len(packages) == 1:
            version = quote(params["version"])
            version_check = f"\ncase \"$manager\" in\n  apt|apt-get) installed=$(dpkg-query -W -f='${{Version}}' {quote(packages[0])} 2>/dev/null) ;;\n  dnf|yum|zypper) installed=$(rpm -q --qf '%{{VERSION}}-%{{RELEASE}}' {quote(packages[0])}) ;;\n  pacman) installed=$(pacman -Q {quote(packages[0])} | awk '{{print $2}}') ;;\n  *) echo \"unsupported package manager: $manager\" >&2; exit 2 ;;\nesac\ntest \"$installed\" = {version}\n"
        command = _inspection_header(params) + f"""
for package in {package_args}; do
  if [ {quote(state)} = installed ]; then
    is_installed "$package"
  else
    ! is_installed "$package"
  fi
done
{version_check}
"""
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.check failed")
