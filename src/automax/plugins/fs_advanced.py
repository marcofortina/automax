# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Advanced filesystem operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



def _diff(path: str, before: str, after: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([before + "\n"], [after + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


class FsBindMountPlugin(BasePlugin):
    name = "storage.mount.bind"
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
            raise PluginValidationError("storage.mount.bind state must be present or absent")
        sudo = sudo_prefix(params, default=True)
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
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="storage.mount.bind failed")


class FsInodeUsageAssertPlugin(BasePlugin):
    name = "storage.usage.inode_check"
    description = "Check remote filesystem inode free and used percentage thresholds."
    required_params = ("path",)
    optional_params = ("max_used_percent", "min_free_percent", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if "max_used_percent" not in params and "min_free_percent" not in params:
            raise PluginValidationError("storage.usage.inode_check requires max_used_percent or min_free_percent")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.usage.inode_check is a read-only inode usage check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        awk_vars = {
            "max_used_percent": params.get("max_used_percent", ""),
            "min_free_percent": params.get("min_free_percent", ""),
        }
        var_args = " ".join(f"-v {name}={quote(value)}" for name, value in awk_vars.items())
        program = (
            'NR==2 {'
            'gsub(/%/, "", $5); '
            'free_percent=($2>0 ? ($4/$2)*100 : 0); '
            'used_percent=$5+0; '
            'ok=1; '
            'if (max_used_percent != "" && used_percent > max_used_percent) ok=0; '
            'if (min_free_percent != "" && free_percent < min_free_percent) ok=0; '
            'printf "free_percent=%.2f used_percent=%.2f\n", free_percent, used_percent; '
            'exit(ok ? 0 : 1)'
            '}'
        )
        return [f"{sudo_prefix(params, default=True)}df -Pi {quote(params['path'])} | awk {var_args} {quote(program)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        command = f"{sudo_prefix(params, default=True)}df -Pi {quote(params['path'])} | awk 'NR==2 {{gsub(/%/, \"\", $5); print $2, $3, $4, $5}}'"
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.usage.inode_check failed")
        try:
            total, used, free, used_percent_raw = [int(item) for item in out.strip().split()[:4]]
        except (ValueError, IndexError) as exc:
            return PluginResult.failure(rc=1, stdout=out, stderr=str(exc), message="storage.usage.inode_check could not parse df output")
        free_percent = (free / total * 100.0) if total else 0.0
        used_percent = float(used_percent_raw)
        data = {"total_inodes": total, "used_inodes": used, "free_inodes": free, "free_percent": free_percent, "used_percent": used_percent}
        if "max_used_percent" in params and used_percent > float(params["max_used_percent"]):
            return PluginResult.failure(message="storage.usage.inode_check used percent threshold failed", data=data)
        if "min_free_percent" in params and free_percent < float(params["min_free_percent"]):
            return PluginResult.failure(message="storage.usage.inode_check free percent threshold failed", data=data)
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data=data)
