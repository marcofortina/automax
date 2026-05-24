# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Filesystem ACL, attribute and quota operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class FsAclPlugin(BasePlugin):
    name = "fs.acl"
    description = "Ensure or remove POSIX ACL entries with getfacl backup support."
    required_params = ("path", "acl")
    optional_params = ("state", "recursive", "backup", "backup_path", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(str(params["path"]), f"{params.get('state', 'present')} {params['acl']}\n", "acl-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("fs.acl state must be present or absent")
        sudo = _sudo(params)
        path = quote(params["path"])
        commands = []
        if bool(params.get("backup", True)):
            backup = str(params.get("backup_path", f"/tmp/automax-acl-{str(params['path']).strip('/').replace('/', '_')}.acl"))
            commands.append(f"{sudo}getfacl -p {path} > {quote(backup)}")
        flag = "-R " if bool(params.get("recursive", False)) else ""
        if state == "present":
            commands.append(f"{sudo}setfacl {flag}-m {quote(params['acl'])} {path}")
        else:
            commands.append(f"{sudo}setfacl {flag}-x {quote(params['acl'])} {path}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="fs.acl failed")


class FsAttrPlugin(BasePlugin):
    name = "fs.attr"
    description = "Set or clear Linux filesystem attributes with chattr."
    required_params = ("path", "attrs")
    optional_params = ("state", "recursive", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _diff(str(params["path"]), f"{params.get('state', 'present')} {params['attrs']}\n", "attr-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("fs.attr state must be present or absent")
        op = "+" if state == "present" else "-"
        flag = "-R " if bool(params.get("recursive", False)) else ""
        return [f"{_sudo(params)}chattr {flag}{op}{quote(params['attrs'])} {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="fs.attr failed")


class FsQuotaPlugin(BasePlugin):
    name = "fs.quota"
    description = "Set user or group filesystem quotas with setquota."
    required_params = ("target", "mountpoint")
    optional_params = ("type", "block_soft", "block_hard", "inode_soft", "inode_hard", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = f"{params.get('type', 'user')} {params['target']} blocks={params.get('block_soft', 0)}/{params.get('block_hard', 0)} inodes={params.get('inode_soft', 0)}/{params.get('inode_hard', 0)}\n"
        return _diff(str(params["mountpoint"]), desired, "quota-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        quota_type = str(params.get("type", "user"))
        if quota_type not in {"user", "group"}:
            raise PluginValidationError("fs.quota type must be user or group")
        flag = "-u" if quota_type == "user" else "-g"
        values = [params.get("block_soft", 0), params.get("block_hard", 0), params.get("inode_soft", 0), params.get("inode_hard", 0)]
        return [f"{_sudo(params)}setquota {flag} {quote(params['target'])} {' '.join(quote(v) for v in values)} {quote(params['mountpoint'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="fs.quota failed")
