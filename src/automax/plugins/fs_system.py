# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Filesystem ACL, attribute and quota operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



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
        sudo = sudo_prefix(params, default=True)
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
        return [f"{sudo_prefix(params, default=True)}chattr {flag}{op}{quote(params['attrs'])} {quote(params['path'])}"]

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
        return [f"{sudo_prefix(params, default=True)}setquota {flag} {quote(params['target'])} {' '.join(quote(v) for v in values)} {quote(params['mountpoint'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="fs.quota failed")


def _acl_entries(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


class FsAclGetPlugin(BasePlugin):
    name = "fs.acl.get"
    description = "Read POSIX ACL entries with getfacl."
    required_params = ("path",)
    optional_params = ("recursive", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        recursive = " -R" if bool(params.get("recursive", False)) else ""
        return [f"{sudo_prefix(params, default=True)}getfacl -p{recursive} {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.acl.get failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"acl": out, "path": params["path"]})


class FsAclAssertPlugin(BasePlugin):
    name = "fs.acl.assert"
    description = "Assert that POSIX ACL entries are present or absent."
    required_params = ("path", "acl")
    optional_params = ("state", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = "\n".join(f"{params.get('state', 'present')} {entry}" for entry in _acl_entries(params["acl"])) + "\n"
        return _diff(str(params["path"]), desired, "acl-assert-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("fs.acl.assert state must be present or absent")
        commands = []
        acl_source = f"{sudo_prefix(params, default=True)}getfacl -cp {quote(params['path'])}"
        for entry in _acl_entries(params["acl"]):
            grep_cmd = f"{acl_source} | grep -Fx -- {quote(entry)} >/dev/null"
            if state == "present":
                commands.append(grep_cmd)
            else:
                commands.append(f"! {grep_cmd}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = " && ".join(self.manual_commands(params, context))
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.acl.assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"path": params["path"], "acl": _acl_entries(params["acl"])})


class FsAclRestorePlugin(BasePlugin):
    name = "fs.acl.restore"
    description = "Restore POSIX ACL entries from a getfacl backup file."
    required_params = ("file",)
    optional_params = ("test_only", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(str(params["file"]), "setfacl --restore\n", "acl-restore-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        test = " --test" if bool(params.get("test_only", False)) else ""
        return [f"{sudo_prefix(params, default=True)}setfacl{test} --restore={quote(params['file'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = self.manual_commands(params, context)[0]
        rc, out, err = exec_remote(context, command)
        stdout = out if bool(params.get("test_only", False)) else f"{out}\n{CHANGE_MARKER}\n"
        return result_from_remote(rc=rc, stdout=stdout if rc == 0 else out, stderr=err, message="fs.acl.restore failed", data={"file": params["file"]})
