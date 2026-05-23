# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux package repository and signing-key management plugins."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file, upload_text_to_temp
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


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
    name = "pkg.key.add"
    description = "Install a package repository signing key for apt or rpm-based systems."
    required_params = ("name",)
    optional_params = ("manager", "url", "content", "src", "dest", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        provided = [bool(params.get(key)) for key in ("url", "content", "src")]
        if sum(provided) != 1:
            raise PluginValidationError("pkg.key.add requires exactly one of url, content or src")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        manager = _manager(params)
        if params.get("url") and manager in {"auto", "dnf", "yum", "rpm"}:
            command = f"{_sudo(params)}rpm --import {quote(params['url'])} && echo {CHANGE_MARKER}"
            rc, out, err = exec_remote(context, command)
            if manager != "auto" or rc == 0:
                return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.key.add failed")
        dest = str(params.get("dest", f"/etc/apt/keyrings/{params['name']}.gpg"))
        if params.get("url"):
            command = f"{_sudo(params)}mkdir -p {quote('/etc/apt/keyrings')} && curl -fsSL {quote(params['url'])} | {_sudo(params)}tee {quote(dest)} >/dev/null && {_sudo(params)}chmod 0644 {quote(dest)} && echo {CHANGE_MARKER}"
            rc, out, err = exec_remote(context, command)
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.key.add failed", data={"path": dest})
        temp_path = upload_text_to_temp(context, _content_from_params(params), encoding="utf-8")
        rc, out, err = install_uploaded_file(context, temp_path, dest, sudo=bool(params.get("sudo", True)), mode="0644", owner="root", group="root")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.key.add failed", data={"path": dest})


class PackageKeyRemovePlugin(BasePlugin):
    name = "pkg.key.remove"
    description = "Remove an apt keyring file."
    required_params = ("name",)
    optional_params = ("dest", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        dest = str(params.get("dest", f"/etc/apt/keyrings/{params['name']}.gpg"))
        command = f"if test -e {quote(dest)}; then {_sudo(params)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.key.remove failed")


class PackageRepoAddPlugin(BasePlugin):
    name = "pkg.repo.add"
    description = "Install an apt, yum or dnf repository definition."
    required_params = ("name",)
    optional_params = ("manager", "repo", "content", "src", "dest", "update_cache", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        provided = [bool(params.get(key)) for key in ("repo", "content", "src")]
        if sum(provided) != 1:
            raise PluginValidationError("pkg.repo.add requires exactly one of repo, content or src")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        manager = str(params.get("manager", "apt" if str(params.get("repo", "")).startswith("deb ") else "dnf"))
        if manager in {"apt", "apt-get", "debian", "ubuntu"}:
            dest = str(params.get("dest", f"/etc/apt/sources.list.d/{params['name']}.list"))
        elif manager in {"dnf", "yum", "redhat", "rhel", "fedora"}:
            dest = str(params.get("dest", f"/etc/yum.repos.d/{params['name']}.repo"))
        else:
            raise PluginValidationError("pkg.repo.add manager must be apt, dnf or yum compatible")
        content = _content_from_params(params, default=str(params.get("repo", "")))
        temp_path = upload_text_to_temp(context, content, encoding="utf-8")
        rc, out, err = install_uploaded_file(context, temp_path, dest, sudo=bool(params.get("sudo", True)), mode="0644", owner="root", group="root")
        if rc == 0 and bool(params.get("update_cache", False)):
            updater = "apt-get update" if dest.endswith(".list") else ("dnf makecache" if manager != "yum" else "yum makecache")
            rc2, out2, err2 = exec_remote(context, f"{_sudo(params)}{updater}")
            rc = rc2
            out += out2
            err += err2
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.repo.add failed", data={"path": dest})


class PackageRepoRemovePlugin(BasePlugin):
    name = "pkg.repo.remove"
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
        command = f"if test -e {quote(dest)}; then {_sudo(params)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
        if bool(params.get("update_cache", False)):
            updater = "apt-get update" if dest.endswith(".list") else ("dnf makecache" if manager != "yum" else "yum makecache")
            command += f"; {_sudo(params)}{updater}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pkg.repo.remove failed")
