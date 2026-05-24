# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Advanced filesystem mount operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _diff(path: str, before: str, after: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([before + "\n"], [after + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class MountRemountPlugin(BasePlugin):
    name = "mount.remount"
    description = "Remount an already mounted filesystem with desired options."
    required_params = ("path",)
    optional_params = ("opts", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(str(params["path"]), "current mount options", str(params.get("opts", "defaults")), "mount-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        opts = str(params.get("opts", "defaults"))
        return [f"{_sudo(params)}mount -o remount,{quote(opts)} {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="mount.remount failed")


class FsResizePlugin(BasePlugin):
    name = "fs.resize"
    description = "Resize a filesystem using the appropriate platform tool."
    required_params = ("device", "fstype")
    optional_params = ("path", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(str(params.get("path") or params["device"]), "current filesystem size", "filesystem grown to available size", "filesystem-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        fstype = str(params["fstype"])
        if fstype == "xfs":
            return [f"{sudo}xfs_growfs {quote(params.get('path', params['device']))}"]
        if fstype in {"ext2", "ext3", "ext4"}:
            return [f"{sudo}resize2fs {quote(params['device'])}"]
        return [f"{sudo}resizefs {quote(params['device'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="fs.resize failed")


class FindmntAssertPlugin(BasePlugin):
    name = "findmnt.assert"
    description = "Assert a mountpoint, source, fstype or options using findmnt."
    required_params = ("path",)
    optional_params = ("src", "fstype", "opts")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "findmnt.assert is a read-only mount assertion with no file diff"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        command = f"findmnt -rn {quote(params['path'])}"
        tests = []
        if params.get("src"):
            tests.append(f"findmnt -rn -o SOURCE {quote(params['path'])} | grep -Fx {quote(params['src'])}")
        if params.get("fstype"):
            tests.append(f"findmnt -rn -o FSTYPE {quote(params['path'])} | grep -Fx {quote(params['fstype'])}")
        if params.get("opts"):
            tests.append(f"findmnt -rn -o OPTIONS {quote(params['path'])} | grep -F {quote(params['opts'])}")
        return [" && ".join([command, *tests])]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="findmnt assertion failed")
        return PluginResult.success(stdout=out, stderr=err)
