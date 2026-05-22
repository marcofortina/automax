# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Local command plugin.
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin


class LocalCommandPlugin(BasePlugin):
    """Execute a command on the controller host."""

    name = "local.command"
    description = "Run a local command on the controller host."
    required_params = ("command",)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)

        command = params["command"]
        cwd = params.get("cwd")
        env = params.get("env")
        shell = bool(params.get("shell", isinstance(command, str)))
        timeout = params.get("timeout", context.command_timeout)

        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        ok = completed.returncode == int(params.get("success_rc", 0))
        if not ok:
            return PluginResult.failure(
                rc=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                message="local command failed",
            )
        return PluginResult.success(
            changed=bool(params.get("changed", True)),
            rc=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
