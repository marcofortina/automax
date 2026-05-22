# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote chown macro plugin.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote


class FsChownPlugin(BasePlugin):
    """Change remote file ownership with idempotent non-recursive checks."""

    name = "fs.chown"
    description = "Set remote file or directory owner/group."
    required_params = ("path",)
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not params.get("owner") and not params.get("group"):
            raise ValueError("plugin 'fs.chown' requires owner, group or both")

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: chown {params.get('path')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        path = quote(params["path"])
        owner = params.get("owner")
        group = params.get("group")
        recursive = bool(params.get("recursive", False))
        owner_group = f"{owner or ''}:{group or ''}"
        chown_flags = "-R " if recursive else ""
        chown_cmd = f"chown {chown_flags}{quote(owner_group)} {path}"
        if recursive:
            command = f"{chown_cmd} && echo {CHANGE_MARKER}"
        else:
            checks = ["test -e {path}".format(path=path)]
            if owner:
                checks.append(f"test \"$(stat -c %U {path})\" = {quote(owner)}")
            if group:
                checks.append(f"test \"$(stat -c %G {path})\" = {quote(group)}")
            command = " && ".join(checks) + f" || {{ {chown_cmd} && echo {CHANGE_MARKER}; }}"
        rc, out, err = exec_remote(context, apply_cwd(command, context, params.get("cwd")))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.chown failed",
            data={"path": params["path"], "owner": owner, "group": group},
        )
