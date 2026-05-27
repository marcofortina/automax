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
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import normalize_env_mapping, render_env_prefix


class LocalCommandPlugin(BasePlugin):
    """Execute a command on the controller host."""

    name = "local.command"
    description = "Run a local command on the controller host."
    required_params = ("command",)
    parameter_schema = {"command": {"types": ("string", "list")}}

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
            if not isinstance(env, dict):
                raise PluginValidationError("local.command env must be a mapping")
            rendered = f"{render_env_prefix(env)} {rendered}"
        return [rendered]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)

        command = params["command"]
        cwd = params.get("cwd")
        env = params.get("env")
        if env is not None:
            if not isinstance(env, dict):
                raise PluginValidationError("local.command env must be a mapping")
            env = normalize_env_mapping(env)
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
