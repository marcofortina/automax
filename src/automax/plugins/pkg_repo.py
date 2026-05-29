# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux package repository and signing-key management plugins."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file, upload_text_to_temp
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, predicate_result_from_remote, quote, result_from_remote, sudo_prefix



def _manager(params: Dict[str, Any]) -> str:
    manager = str(params.get("manager", "auto"))
    if manager != "auto":
        return manager
    return "auto"


def _content_from_params(params: Dict[str, Any], *, default: str = "") -> str:
    if params.get("content") is not None:
        return str(params["content"]).rstrip() + "\n"
    if params.get("src"):
        return Path(str(params["src"])).expanduser().read_text(encoding="utf-8")
    return default.rstrip() + "\n"


class PackageKeyAddPlugin(BasePlugin):
    name = "os.package.key.add"
    description = "Install a package repository signing key for apt or rpm-based systems."
    required_params = ("name",)
    optional_params = ("manager", "url", "content", "src", "dest", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        provided = [bool(params.get(key)) for key in ("url", "content", "src")]
        if sum(provided) != 1:
            raise PluginValidationError("os.package.key.add requires exactly one of url, content or src")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        manager = _manager(params)
        if params.get("url") and manager in {"auto", "dnf", "yum", "rpm"}:
            command = f"{sudo_prefix(params, default=True)}rpm --import {quote(params['url'])} && echo {CHANGE_MARKER}"
            rc, out, err = exec_remote(context, command)
            if manager != "auto" or rc == 0:
                return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.key.add failed")
        dest = str(params.get("dest", f"/etc/apt/keyrings/{params['name']}.gpg"))
        if params.get("url"):
            command = f"{sudo_prefix(params, default=True)}mkdir -p {quote('/etc/apt/keyrings')} && curl -fsSL {quote(params['url'])} | {sudo_prefix(params, default=True)}tee {quote(dest)} >/dev/null && {sudo_prefix(params, default=True)}chmod 0644 {quote(dest)} && echo {CHANGE_MARKER}"
            rc, out, err = exec_remote(context, command)
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.key.add failed", data={"path": dest})
        temp_path = upload_text_to_temp(context, _content_from_params(params), encoding="utf-8")
        rc, out, err = install_uploaded_file(context, temp_path, dest, sudo=bool(params.get("sudo", True)), mode="0644", owner="root", group="root")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.key.add failed", data={"path": dest})


class PackageKeyRemovePlugin(BasePlugin):
    name = "os.package.key.remove"
    description = "Remove an apt keyring file."
    required_params = ("name",)
    optional_params = ("dest", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        dest = str(params.get("dest", f"/etc/apt/keyrings/{params['name']}.gpg"))
        command = f"if test -e {quote(dest)}; then {sudo_prefix(params, default=True)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.key.remove failed")


class PackageRepoAddPlugin(BasePlugin):
    name = "os.package.repo.add"
    description = "Install an apt, yum or dnf repository definition."
    required_params = ("name",)
    optional_params = ("manager", "repo", "content", "src", "dest", "update_cache", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        provided = [bool(params.get(key)) for key in ("repo", "content", "src")]
        if sum(provided) != 1:
            raise PluginValidationError("os.package.repo.add requires exactly one of repo, content or src")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        manager = str(params.get("manager", "apt" if str(params.get("repo", "")).startswith("deb ") else "dnf"))
        if manager in {"apt", "apt-get", "debian", "ubuntu"}:
            dest = str(params.get("dest", f"/etc/apt/sources.list.d/{params['name']}.list"))
        elif manager in {"dnf", "yum", "redhat", "rhel", "fedora"}:
            dest = str(params.get("dest", f"/etc/yum.repos.d/{params['name']}.repo"))
        else:
            raise PluginValidationError("os.package.repo.add manager must be apt, dnf or yum compatible")
        content = _content_from_params(params, default=str(params.get("repo", "")))
        temp_path = upload_text_to_temp(context, content, encoding="utf-8")
        rc, out, err = install_uploaded_file(context, temp_path, dest, sudo=bool(params.get("sudo", True)), mode="0644", owner="root", group="root")
        if rc == 0 and bool(params.get("update_cache", False)):
            updater = "apt-get update" if dest.endswith(".list") else ("dnf makecache" if manager != "yum" else "yum makecache")
            rc2, out2, err2 = exec_remote(context, f"{sudo_prefix(params, default=True)}{updater}")
            rc = rc2
            out += out2
            err += err2
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.repo.add failed", data={"path": dest})


class PackageRepoRemovePlugin(BasePlugin):
    name = "os.package.repo.remove"
    description = "Remove an apt, yum or dnf repository definition."
    required_params = ("name",)
    optional_params = ("manager", "dest", "update_cache", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        manager = str(params.get("manager", "apt"))
        if params.get("dest"):
            dest = str(params["dest"])
        elif manager in {"apt", "apt-get", "debian", "ubuntu"}:
            dest = f"/etc/apt/sources.list.d/{params['name']}.list"
        else:
            dest = f"/etc/yum.repos.d/{params['name']}.repo"
        command = f"if test -e {quote(dest)}; then {sudo_prefix(params, default=True)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
        if bool(params.get("update_cache", False)):
            updater = "apt-get update" if dest.endswith(".list") else ("dnf makecache" if manager != "yum" else "yum makecache")
            command += f"; {sudo_prefix(params, default=True)}{updater}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.repo.remove failed")


class PackageRepoListPlugin(BasePlugin):
    name = "os.package.repo.list"
    description = "List package repository definition files."
    optional_params = ("manager", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        manager = str(params.get("manager", "auto"))
        return [
            "case " + quote(manager) + " in "
            "auto|apt|apt-get|debian|ubuntu) find /etc/apt/sources.list /etc/apt/sources.list.d -maxdepth 1 -type f 2>/dev/null | sort ;; "
            "dnf|yum|redhat|rhel|fedora) find /etc/yum.repos.d -maxdepth 1 -type f -name '*.repo' 2>/dev/null | sort ;; "
            "*) echo 'unsupported package repository manager' >&2; exit 2 ;; esac"
        ]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        repos = [line.strip() for line in out.splitlines() if line.strip()] if rc == 0 else []
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.repo.list failed", data={"repositories": repos})


class PackageRepoCheckPlugin(BasePlugin):
    name = "os.package.repo.check"
    description = "Check whether a package repository definition file exists and optionally contains text."
    required_params = ("name",)
    optional_params = ("manager", "dest", "contains", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def _dest(self, params: Dict[str, Any]) -> str:
        if params.get("dest"):
            return str(params["dest"])
        manager = str(params.get("manager", "apt"))
        if manager in {"apt", "apt-get", "debian", "ubuntu"}:
            return f"/etc/apt/sources.list.d/{params['name']}.list"
        return f"/etc/yum.repos.d/{params['name']}.repo"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        dest = self._dest(params)
        command = f"test -f {quote(dest)}"
        if params.get("contains"):
            command += f" && grep -F -- {quote(params['contains'])} {quote(dest)} >/dev/null"
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.package.repo.check failed",
            data_key="matches",
            data={"path": self._dest(params)},
        )


class PackageKeyListPlugin(BasePlugin):
    name = "os.package.key.list"
    description = "List package repository signing key files."
    optional_params = ("manager", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return ["find /etc/apt/keyrings /usr/share/keyrings -maxdepth 1 -type f 2>/dev/null | sort"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        keys = [line.strip() for line in out.splitlines() if line.strip()] if rc == 0 else []
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.package.key.list failed", data={"keys": keys})


class PackageKeyCheckPlugin(BasePlugin):
    name = "os.package.key.check"
    description = "Check whether a package repository signing key file exists."
    required_params = ("name",)
    optional_params = ("dest", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def _dest(self, params: Dict[str, Any]) -> str:
        return str(params.get("dest", f"/etc/apt/keyrings/{params['name']}.gpg"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"test -f {quote(self._dest(params))}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="os.package.key.check failed",
            data_key="exists",
            data={"path": self._dest(params)},
        )
