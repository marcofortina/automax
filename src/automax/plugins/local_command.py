# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Local command plugin.
"""

from __future__ import annotations

import shlex
import subprocess
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin


class LocalCommandPlugin(BasePlugin):
    """Execute a command on the controller host."""

    name = "local.command"
    description = "Run a local command on the controller host."
    required_params = ("command",)

    def manual_commands(
        self, params: Dict[str, Any], context: ExecutionContext
    ) -> list[str]:
        self.validate(params)
        command = params["command"]
        if isinstance(command, list):
            rendered = " ".join(shlex.quote(str(item)) for item in command)
        else:
            rendered = str(command)
        if params.get("cwd"):
            rendered = f"cd {shlex.quote(str(params['cwd']))} && {rendered}"
        if params.get("env"):
            env = params["env"]
            if isinstance(env, dict):
                prefix = " ".join(
                    f"{key}={shlex.quote(str(value))}" for key, value in sorted(env.items())
                )
                rendered = f"{prefix} {rendered}"
        return [rendered]

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
