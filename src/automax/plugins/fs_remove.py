"""
Remote filesystem remove macro plugin.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote


class FsRemovePlugin(BasePlugin):
    """Remove a remote file or directory idempotently."""

    name = "fs.remove"
    description = "Remove a remote file or directory when present."
    required_params = ("path",)
    optional_params = ("recursive", "force", "cwd")
    opens_remote_session = True

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: remove {params.get('path')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="fs.remove requires an SSH session")

        path = quote(params["path"])
        flags = []
        if bool(params.get("recursive", False)):
            flags.append("-r")
        if bool(params.get("force", False)):
            flags.append("-f")
        flag_text = "".join(flags)
        remove_cmd = f"rm {flag_text} {path}" if flag_text else f"rm {path}"
        command = f"test ! -e {path} || {{ {remove_cmd} && echo {CHANGE_MARKER}; }}"
        rc, out, err = exec_remote(context, apply_cwd(command, context, params.get("cwd")))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.remove failed",
            data={"path": params["path"]},
        )
