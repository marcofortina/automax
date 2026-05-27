# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Filesystem mkdir macro plugin.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote, sudo_prefix


class FsMkdirPlugin(BasePlugin):
    """Create a directory locally or remotely with readable parameters."""

    name = "fs.mkdir"
    description = "Create a directory with owner/group/mode parameters."
    required_params = ("path",)
    optional_params = ("mode", "owner", "group", "cwd", "sudo")
    opens_remote_session = True

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        path = quote(params["path"])
        mode = params.get("mode")
        owner = params.get("owner")
        group = params.get("group")

        checks = [f"test -d {path}"]
        if mode:
            checks.append(f'test "$(stat -c %a {path})" = {quote(mode)}')
        if owner:
            checks.append(f'test "$(stat -c %U {path})" = {quote(owner)}')
        if group:
            checks.append(f'test "$(stat -c %G {path})" = {quote(group)}')

        sudo = sudo_prefix(params, default=False)
        commands = [f"{sudo}mkdir -p {path}"]
        if mode:
            commands.append(f"{sudo}chmod {quote(mode)} {path}")
        if owner or group:
            owner_group = f"{owner or ''}:{group or ''}"
            commands.append(f"{sudo}chown {quote(owner_group)} {path}")

        command = (
            " && ".join(checks)
            + " || { "
            + " && ".join(commands)
            + f"; echo {CHANGE_MARKER}; }}"
        )
        return apply_cwd(command, context, params.get("cwd"))

    def manual_commands(
        self, params: Dict[str, Any], context: ExecutionContext
    ) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: create directory {params.get('path')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="fs.mkdir requires an SSH session")

        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.mkdir failed",
            data={"path": params["path"]},
        )
