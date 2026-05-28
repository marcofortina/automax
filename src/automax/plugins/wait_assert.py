# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote disk assertion plugin."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import exec_remote, quote, sudo_prefix


class AssertDiskPlugin(BasePlugin):
    """Assert disk capacity thresholds for a remote filesystem path."""

    name = "assert.disk"
    description = "Assert remote disk capacity thresholds."
    required_params = ("path",)
    optional_params = ("min_free_mb", "min_free_percent", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if "min_free_mb" not in params and "min_free_percent" not in params:
            raise PluginValidationError("assert.disk requires min_free_mb or min_free_percent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        command = f"{sudo_prefix(params, default=False)}df -Pk {quote(params['path'])} | awk 'NR==2 {{print $2, $4}}'"
        rc, out, err = exec_remote(context, command, get_pty=bool(params.get("sudo", False)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="assert.disk failed")
        try:
            total_kb, free_kb = [int(item) for item in out.strip().split()[:2]]
        except (ValueError, IndexError) as exc:
            return PluginResult.failure(
                rc=1,
                stdout=out,
                stderr=str(exc),
                message="assert.disk could not parse df output",
            )
        free_mb = free_kb // 1024
        free_percent = (free_kb / total_kb * 100.0) if total_kb else 0.0
        if "min_free_mb" in params and free_mb < int(params["min_free_mb"]):
            return PluginResult.failure(
                message="assert.disk free MB threshold failed",
                data={"free_mb": free_mb, "free_percent": free_percent},
            )
        if "min_free_percent" in params and free_percent < float(params["min_free_percent"]):
            return PluginResult.failure(
                message="assert.disk free percent threshold failed",
                data={"free_mb": free_mb, "free_percent": free_percent},
            )
        return PluginResult.success(
            changed=False,
            data={"free_mb": free_mb, "free_percent": free_percent},
        )
