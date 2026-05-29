# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote chown plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote, sudo_prefix


def _require_owner_or_group(plugin_name: str, params: Dict[str, Any]) -> None:
    if not params.get("owner") and not params.get("group"):
        raise PluginValidationError(f"plugin '{plugin_name}' requires owner, group or both")


class FsChownPlugin(BasePlugin):
    """Change remote file ownership with idempotent non-recursive checks."""

    name = "fs.permission.owner.set"
    description = "Set remote file or directory owner/group."
    required_params = ("path",)
    optional_params = ("owner", "group", "recursive", "sudo", "cwd")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _require_owner_or_group(self.name, params)

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: chown {params.get('path')}",
            data={"params": params},
        )

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        path = quote(params["path"])
        owner = params.get("owner")
        group = params.get("group")
        recursive = bool(params.get("recursive", False))
        sudo = sudo_prefix(params, default=False)
        owner_group = f"{owner or ''}:{group or ''}"
        chown_flags = "-R " if recursive else ""
        chown_cmd = f"{sudo}chown {chown_flags}{quote(owner_group)} {path}"
        if recursive:
            command = f"{chown_cmd} && echo {CHANGE_MARKER}"
        else:
            checks = [f"test -e {path}"]
            if owner:
                checks.append(f"test \"$(stat -c %U {path})\" = {quote(owner)}")
            if group:
                checks.append(f"test \"$(stat -c %G {path})\" = {quote(group)}")
            command = " && ".join(checks) + f" || {{ {chown_cmd} && echo {CHANGE_MARKER}; }}"
        return apply_cwd(command, context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.permission.owner.set failed",
            data={"path": params["path"], "owner": params.get("owner"), "group": params.get("group")},
        )


class FsOwnerGetPlugin(BasePlugin):
    """Read a remote file or directory owner and group."""

    name = "fs.permission.owner.get"
    description = "Read remote file or directory owner and group."
    required_params = ("path",)
    optional_params = ("cwd",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [apply_cwd(f"stat -c '%U|%G' {quote(params['path'])}", context, params.get("cwd"))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = self.manual_commands(params, context)[0]
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.permission.owner.get failed")
        owner, group = (out.strip().split("|", 1) + [""])[:2]
        return PluginResult.success(changed=False, rc=rc, stdout=out, data={"path": params["path"], "owner": owner, "group": group})


class FsOwnerCheckPlugin(BasePlugin):
    """Check remote file ownership without failing on mismatches."""

    name = "fs.permission.owner.check"
    description = "Check remote file or directory owner/group."
    required_params = ("path",)
    optional_params = ("owner", "group", "cwd")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _require_owner_or_group(self.name, params)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [apply_cwd(f"test -e {quote(params['path'])} && stat -c '%U|%G' {quote(params['path'])} || true", context, params.get("cwd"))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        path = quote(params["path"])
        command = apply_cwd(f"if test -e {path}; then stat -c '%U|%G' {path}; else exit 10; fi", context, params.get("cwd"))
        rc, out, err = exec_remote(context, command)
        if rc == 10:
            return PluginResult.success(changed=False, rc=0, data={"path": params["path"], "owner": params.get("owner"), "group": params.get("group"), "exists": False, "matches": False})
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.permission.owner.check failed")
        current_owner, current_group = (out.strip().split("|", 1) + [""])[:2]
        matches = True
        if params.get("owner") is not None and current_owner != str(params["owner"]):
            matches = False
        if params.get("group") is not None and current_group != str(params["group"]):
            matches = False
        return PluginResult.success(
            changed=False,
            rc=0,
            stdout=out,
            data={
                "path": params["path"],
                "owner": params.get("owner"),
                "group": params.get("group"),
                "current_owner": current_owner,
                "current_group": current_group,
                "exists": True,
                "matches": matches,
            },
        )
