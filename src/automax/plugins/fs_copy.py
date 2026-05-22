# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote filesystem copy macro plugin.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote


class FsCopyPlugin(BasePlugin):
    """Copy files or directories on the remote target."""

    name = "fs.copy"
    description = "Copy a remote file or directory to another remote path."
    required_params = ("src", "dest")
    optional_params = (
        "recursive",
        "preserve",
        "overwrite",
        "creates",
        "mode",
        "owner",
        "group",
        "cwd",
    )
    opens_remote_session = True

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: copy {params.get('src')} to {params.get('dest')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="fs.copy requires an SSH session")

        src = quote(params["src"])
        dest = quote(params["dest"])
        flags = []
        if bool(params.get("recursive", False)):
            flags.append("-R")
        if bool(params.get("preserve", False)):
            flags.append("-p")
        overwrite = bool(params.get("overwrite", True))
        if not overwrite:
            flags.append("-n")
        flag_text = " ".join(flags)
        copy_cmd = f"cp {flag_text} {src} {dest}" if flag_text else f"cp {src} {dest}"

        post_commands = []
        if params.get("mode"):
            post_commands.append(f"chmod {quote(params['mode'])} {dest}")
        if params.get("owner") or params.get("group"):
            owner_group = f"{params.get('owner') or ''}:{params.get('group') or ''}"
            post_commands.append(f"chown {quote(owner_group)} {dest}")

        commands = [copy_cmd, *post_commands, f"echo {CHANGE_MARKER}"]
        body = " && ".join(commands)
        guard = params.get("creates")
        if guard:
            command = f"test -e {quote(guard)} || {{ {body}; }}"
        elif not overwrite:
            command = f"test -e {dest} || {{ {body}; }}"
        else:
            command = f"{{ {body}; }}"

        rc, out, err = exec_remote(context, apply_cwd(command, context, params.get("cwd")))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.copy failed",
            data={"src": params["src"], "dest": params["dest"]},
        )
