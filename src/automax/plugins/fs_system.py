# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Filesystem ACL, attribute and quota operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, predicate_result_from_remote, quote, result_from_remote, sudo_prefix



def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class FsAclPlugin(BasePlugin):
    name = "fs.acl.set"
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
            raise PluginValidationError("fs.acl.set state must be present or absent")
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
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="fs.acl.set failed")


class FsAttrPlugin(BasePlugin):
    name = "fs.attr.set"
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
            raise PluginValidationError("fs.attr.set state must be present or absent")
        op = "+" if state == "present" else "-"
        flag = "-R " if bool(params.get("recursive", False)) else ""
        return [f"{sudo_prefix(params, default=True)}chattr {flag}{op}{quote(params['attrs'])} {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="fs.attr.set failed")


def _attr_entries(value: Any) -> list[str]:
    return [char for char in str(value) if char not in {"+", "-", "=", ",", " "}]


class FsAttrGetPlugin(BasePlugin):
    name = "fs.attr.get"
    description = "Read Linux filesystem attributes with lsattr."
    required_params = ("path",)
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}lsattr -d {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.attr.get failed")
        attrs = out.split(None, 1)[0] if out.split() else ""
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"attrs": attrs, "path": params["path"]})


class FsAttrCheckPlugin(BasePlugin):
    name = "fs.attr.check"
    description = "Check whether Linux filesystem attributes are present or absent."
    required_params = ("path", "attrs")
    optional_params = ("state", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(str(params["path"]), f"{params.get('state', 'present')} {params['attrs']}\n", "attr-check-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("fs.attr.check state must be present or absent")
        attrs = _attr_entries(params["attrs"])
        if not attrs:
            raise PluginValidationError("fs.attr.check attrs must contain at least one attribute")
        checks = []
        attr_source = f"{sudo_prefix(params, default=True)}lsattr -d {quote(params['path'])} | awk '{{print $1}}'"
        for attr in attrs:
            grep_cmd = f"{attr_source} | grep -F -- {quote(attr)} >/dev/null"
            checks.append(grep_cmd if state == "present" else f"! {grep_cmd}")
        return checks

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = " && ".join(self.manual_commands(params, context))
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.attr.check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"path": params["path"], "attrs": _attr_entries(params["attrs"])})


class FsQuotaPlugin(BasePlugin):
    parameter_schema = {"type": {"enum": ["user", "group"], "default": "user", "description": "Quota subject type."}}
    name = "storage.quota.set"
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
            raise PluginValidationError("storage.quota.set type must be user or group")
        flag = "-u" if quota_type == "user" else "-g"
        values = [params.get("block_soft", 0), params.get("block_hard", 0), params.get("inode_soft", 0), params.get("inode_hard", 0)]
        return [f"{sudo_prefix(params, default=True)}setquota {flag} {quote(params['target'])} {' '.join(quote(v) for v in values)} {quote(params['mountpoint'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.quota.set failed")


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
    name = "fs.acl.check"
    description = "Check whether POSIX ACL entries are present or absent."
    required_params = ("path", "acl")
    optional_params = ("state", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = "\n".join(f"{params.get('state', 'present')} {entry}" for entry in _acl_entries(params["acl"])) + "\n"
        return _diff(str(params["path"]), desired, "acl-check-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("fs.acl.check state must be present or absent")
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
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.acl.check failed")
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


def _quota_flag(params: Dict[str, Any]) -> str:
    quota_type = str(params.get("type", "user"))
    if quota_type not in {"user", "group"}:
        raise PluginValidationError("storage.quota type must be user or group")
    return "-u" if quota_type == "user" else "-g"


class StorageQuotaGetPlugin(BasePlugin):
    parameter_schema = {"type": {"enum": ["user", "group"], "default": "user", "description": "Quota subject type."}}
    name = "storage.quota.get"
    description = "Read one user or group quota entry from a mounted filesystem."
    required_params = ("target", "mountpoint")
    optional_params = ("type", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.quota.get is a read-only quota query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        flag = _quota_flag(params)
        return [f"{sudo_prefix(params, default=True)}repquota -P {flag} {quote(params['mountpoint'])} | awk -v target={quote(params['target'])} '$1 == target {{print}}'"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.quota.get failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"quota": out.strip(), "target": params["target"], "mountpoint": params["mountpoint"]})


class StorageQuotaCheckPlugin(BasePlugin):
    parameter_schema = {"type": {"enum": ["user", "group"], "default": "user", "description": "Quota subject type."}}
    name = "storage.quota.check"
    description = "Check user or group quota limits on a mounted filesystem."
    required_params = ("target", "mountpoint")
    optional_params = ("type", "block_soft", "block_hard", "inode_soft", "inode_hard", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not any(key in params for key in ("block_soft", "block_hard", "inode_soft", "inode_hard")):
            raise PluginValidationError("storage.quota.check requires at least one quota limit")
        _quota_flag(params)

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.quota.check is a read-only quota check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        flag = _quota_flag(params)
        target = quote(params["target"])
        quota_line = f"{sudo_prefix(params, default=True)}repquota -P {flag} {quote(params['mountpoint'])} | awk -v target={target} '$1 == target {{print}}'"
        checks = [f"line=$({quota_line}); test -n \"$line\""]
        fields = {"block_soft": 4, "block_hard": 5, "inode_soft": 8, "inode_hard": 9}
        for key, field in fields.items():
            if key in params:
                checks.append(f"printf '%s\n' \"$line\" | awk '{{print ${field}}}' | grep -Fx -- {quote(params[key])}")
        return [" && ".join(checks)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return predicate_result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="storage.quota.check failed",
            data_key="matches",
            data={"target": str(params["target"]), "mountpoint": str(params["mountpoint"])},
        )


class StorageQuotaFactsPlugin(BasePlugin):
    parameter_schema = {"type": {"enum": ["user", "group"], "default": "user", "description": "Quota subject type."}}
    name = "storage.quota.facts"
    description = "Collect user or group quota facts from a mounted filesystem."
    required_params = ("mountpoint",)
    optional_params = ("type", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.quota.facts is a read-only quota facts query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        flag = _quota_flag(params)
        return [f"{sudo_prefix(params, default=True)}repquota -P {flag} {quote(params['mountpoint'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.quota.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"quotas": out})
