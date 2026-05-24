# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Advanced filesystem operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _diff(path: str, before: str, after: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([before + "\n"], [after + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class FsBindMountPlugin(BasePlugin):
    name = "fs.bind_mount"
    description = "Ensure a runtime and optional persistent bind mount."
    required_params = ("src", "dest")
    optional_params = ("state", "opts", "persist", "runtime", "sudo")
    opens_remote_session = True

    def _entry(self, params: Dict[str, Any]) -> str:
        opts = str(params.get("opts", "bind"))
        if "bind" not in opts.split(","):
            opts = "bind," + opts
        return f"{params['src']} {params['dest']} none {opts} 0 0"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff("/etc/fstab", "current fstab", self._entry(params), "bind-mount-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("fs.bind_mount state must be present or absent")
        sudo = _sudo(params)
        src = str(params["src"])
        dest = str(params["dest"])
        commands: list[str] = []
        if state == "present":
            if bool(params.get("runtime", True)):
                commands.extend([f"{sudo}mkdir -p {quote(dest)}", f"findmnt -rn --target {quote(dest)} >/dev/null || {sudo}mount --bind {quote(src)} {quote(dest)}"])
            if bool(params.get("persist", False)):
                entry = self._entry(params)
                commands.append(f"grep -Fqx -- {quote(entry)} /etc/fstab || printf '%s\\n' {quote(entry)} | {sudo}tee -a /etc/fstab >/dev/null")
        else:
            commands.append(f"findmnt -rn --target {quote(dest)} >/dev/null && {sudo}umount {quote(dest)} || true")
            if bool(params.get("persist", False)):
                commands.append(f"{sudo}sed -i.bak {quote('/ ')} /etc/fstab")
                commands[-1] = f"{sudo}sed -i.bak '\\#{quote(src)[1:-1] if quote(src).startswith(chr(39)) else src} {quote(dest)[1:-1] if quote(dest).startswith(chr(39)) else dest} none .*bind.*#d' /etc/fstab"
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="fs.bind_mount failed")

class FsDiskUsageAssertPlugin(BasePlugin):
    name = "fs.disk_usage_assert"
    description = "Assert that filesystem block usage is below a maximum percentage."
    required_params = ("path", "max_percent")
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "fs.disk_usage_assert is a read-only df assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"usage=$({_sudo(params)}df -P {quote(params['path'])} | awk 'NR==2 {{gsub(/%/, \"\", $5); print $5}}'); test \"$usage\" -le {quote(params['max_percent'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.disk_usage_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)

class FsInodeUsageAssertPlugin(BasePlugin):
    name = "fs.inode_usage_assert"
    description = "Assert that filesystem inode usage is below a maximum percentage."
    required_params = ("path", "max_percent")
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "fs.inode_usage_assert is a read-only df -i assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"usage=$({_sudo(params)}df -Pi {quote(params['path'])} | awk 'NR==2 {{gsub(/%/, \"\", $5); print $5}}'); test \"$usage\" -le {quote(params['max_percent'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.inode_usage_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
