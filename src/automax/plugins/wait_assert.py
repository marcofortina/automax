# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote storage usage check plugin."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import exec_remote, quote, sudo_prefix


class AssertDiskPlugin(BasePlugin):
    """Check disk capacity thresholds for a remote filesystem path."""

    name = "storage.usage.disk_check"
    description = "Check remote filesystem free space and used percentage thresholds."
    required_params = ("path",)
    optional_params = ("min_free_mb", "min_free_percent", "max_used_percent", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not any(key in params for key in ("min_free_mb", "min_free_percent", "max_used_percent")):
            raise PluginValidationError("storage.usage.disk_check requires min_free_mb, min_free_percent or max_used_percent")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.usage.disk_check is a read-only disk usage check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=False)
        awk_vars = {
            "min_free_mb": params.get("min_free_mb", ""),
            "min_free_percent": params.get("min_free_percent", ""),
            "max_used_percent": params.get("max_used_percent", ""),
        }
        var_args = " ".join(f"-v {name}={quote(value)}" for name, value in awk_vars.items())
        program = (
            'NR==2 {'
            'gsub(/%/, "", $5); '
            'free_mb=int($4/1024); '
            'free_percent=($2>0 ? ($4/$2)*100 : 0); '
            'used_percent=$5+0; '
            'ok=1; '
            'if (min_free_mb != "" && free_mb < min_free_mb) ok=0; '
            'if (min_free_percent != "" && free_percent < min_free_percent) ok=0; '
            'if (max_used_percent != "" && used_percent > max_used_percent) ok=0; '
            'printf "free_mb=%d free_percent=%.2f used_percent=%.2f\n", free_mb, free_percent, used_percent; '
            'exit(ok ? 0 : 1)'
            '}'
        )
        return [f"{sudo}df -Pk {quote(params['path'])} | awk {var_args} {quote(program)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        command = f"{sudo_prefix(params, default=False)}df -Pk {quote(params['path'])} | awk 'NR==2 {{gsub(/%/, \"\", $5); print $2, $3, $4, $5}}'"
        rc, out, err = exec_remote(context, command, get_pty=bool(params.get("sudo", False)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.usage.disk_check failed")
        try:
            total_kb, used_kb, free_kb, used_percent_raw = [int(item) for item in out.strip().split()[:4]]
        except (ValueError, IndexError) as exc:
            return PluginResult.failure(
                rc=1,
                stdout=out,
                stderr=str(exc),
                message="storage.usage.disk_check could not parse df output",
            )
        free_mb = free_kb // 1024
        free_percent = (free_kb / total_kb * 100.0) if total_kb else 0.0
        used_percent = float(used_percent_raw)
        data = {
            "total_kb": total_kb,
            "used_kb": used_kb,
            "free_kb": free_kb,
            "free_mb": free_mb,
            "free_percent": free_percent,
            "used_percent": used_percent,
        }
        compliant = True
        if "min_free_mb" in params and free_mb < int(params["min_free_mb"]):
            compliant = False
        if "min_free_percent" in params and free_percent < float(params["min_free_percent"]):
            compliant = False
        if "max_used_percent" in params and used_percent > float(params["max_used_percent"]):
            compliant = False
        data["compliant"] = compliant
        return PluginResult.success(changed=False, data=data)
