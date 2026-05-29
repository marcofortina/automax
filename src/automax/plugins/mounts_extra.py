# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Advanced filesystem mount operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



def _diff(path: str, before: str, after: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([before + "\n"], [after + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class MountRemountPlugin(BasePlugin):
    name = "storage.mount.remount"
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
        return [f"{sudo_prefix(params, default=True)}mount -o remount,{quote(opts)} {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.mount.remount failed")


class FsResizePlugin(BasePlugin):
    name = "storage.fs.resize"
    description = "Resize a filesystem using the appropriate platform tool."
    required_params = ("device", "fstype")
    optional_params = ("path", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(str(params.get("path") or params["device"]), "current filesystem size", "filesystem grown to available size", "filesystem-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
        fstype = str(params["fstype"])
        if fstype == "xfs":
            return [f"{sudo}xfs_growfs {quote(params.get('path', params['device']))}"]
        if fstype in {"ext2", "ext3", "ext4"}:
            return [f"{sudo}resize2fs {quote(params['device'])}"]
        return [f"{sudo}resizefs {quote(params['device'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.fs.resize failed")



class FindmntAssertPlugin(BasePlugin):
    name = "storage.mount.check"
    description = "Check runtime mount state by mountpoint, source, fstype or options using findmnt."
    required_params: tuple[str, ...] = ()
    optional_params = ("path", "src", "fstype", "opts", "state", "sudo")
    parameter_schema = {
        "path": {"type": "path", "description": "Optional mountpoint path to match."},
        "src": {"type": "path", "description": "Optional mount source/device to match."},
        "fstype": {"type": "string", "description": "Optional filesystem type to match."},
        "opts": {"type": "string", "description": "Optional mount option to match."},
        "state": {"type": "string", "enum": ["mounted", "unmounted"], "default": "mounted", "description": "Expected runtime mount state."},
    }
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        state = str(params.get("state", "mounted"))
        if state not in {"mounted", "unmounted"}:
            raise PluginValidationError("storage.mount.check state must be mounted or unmounted")
        if not (params.get("path") or params.get("src")):
            raise PluginValidationError("storage.mount.check requires path or src")
        if state == "unmounted" and (params.get("fstype") or params.get("opts")):
            raise PluginValidationError("storage.mount.check fstype/opts require state=mounted")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.mount.check is a read-only runtime mount check with no file diff"

    def _base_command(self, params: Dict[str, Any]) -> str:
        sudo = sudo_prefix(params, default=True)
        source = params.get("src")
        path = params.get("path")
        if source and path:
            return f"{sudo}findmnt -rn -S {quote(source)} -T {quote(path)} >/dev/null"
        if source:
            return f"{sudo}findmnt -rn -S {quote(source)} >/dev/null"
        return f"{sudo}findmnt -rn {quote(path)} >/dev/null"

    def _mounted_tests(self, params: Dict[str, Any]) -> list[str]:
        sudo = sudo_prefix(params, default=True)
        path = params.get("path")
        tests: list[str] = []
        if path and params.get("src"):
            tests.append(f"{sudo}findmnt -rn -o SOURCE {quote(path)} | grep -Fx -- {quote(params['src'])}")
        if path and params.get("fstype"):
            tests.append(f"{sudo}findmnt -rn -o FSTYPE {quote(path)} | grep -Fx -- {quote(params['fstype'])}")
        if path and params.get("opts"):
            tests.append(f"{sudo}findmnt -rn -o OPTIONS {quote(path)} | tr ',' '\\n' | grep -Fx -- {quote(params['opts'])}")
        return tests

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "mounted"))
        command = " && ".join([self._base_command(params), *self._mounted_tests(params)])
        if state == "mounted":
            return [command]
        return [f"{command}; rc=$?; [ $rc -eq 1 ]"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "mounted"))
        command = " && ".join([self._base_command(params), *self._mounted_tests(params)])
        rc, out, err = exec_remote(context, command)
        if rc not in {0, 1}:
            return PluginResult.failure(
                rc=rc,
                stdout=out,
                stderr=err,
                message="storage.mount.check failed",
                data={"path": params.get("path"), "src": params.get("src"), "state": state},
            )
        mounted = rc == 0
        matches = mounted if state == "mounted" else not mounted
        return PluginResult.success(
            changed=False,
            rc=0,
            stdout=out,
            stderr=err if matches else "",
            data={"path": params.get("path"), "src": params.get("src"), "state": state, "mounted": mounted, "matches": matches},
        )
