# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote SSH command plugin.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import apply_cwd


class RemoteCommandPlugin(BasePlugin):
    """Execute a command through the step-scoped SSH connection."""

    name = "remote.command"
    description = "Run a command on the current remote target via SSH."
    required_params = ("command",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="remote.command requires an SSH session")

        command = apply_cwd(str(params["command"]), context, params.get("cwd"))
        timeout = params.get("timeout")
        stdin, stdout, stderr = context.ssh_client.exec_command(
            command,
            timeout=timeout,
            get_pty=bool(params.get("pty", False)),
        )
        if params.get("stdin"):
            stdin.write(str(params["stdin"]))
            stdin.channel.shutdown_write()

        rc = stdout.channel.recv_exit_status()
        out = stdout.read().decode(params.get("encoding", "utf-8"), errors="replace")
        err = stderr.read().decode(params.get("encoding", "utf-8"), errors="replace")
        ok = rc == int(params.get("success_rc", 0))
        if not ok:
            return PluginResult.failure(
                rc=rc,
                stdout=out,
                stderr=err,
                message="remote command failed",
            )
        return PluginResult.success(
            changed=bool(params.get("changed", True)),
            rc=rc,
            stdout=out,
            stderr=err,
        )
