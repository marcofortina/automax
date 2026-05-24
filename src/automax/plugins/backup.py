# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Operational backup and restore plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _checksum_cmd(path: str, params: Dict[str, Any]) -> str:
    checksum = str(params.get("checksum", "sha256"))
    if checksum == "none":
        return "true"
    if checksum != "sha256":
        raise PluginValidationError("checksum must be sha256 or none")
    return f"sha256sum {quote(path)} > {quote(path + '.sha256')}"


class BackupFilePlugin(BasePlugin):
    name = "backup.file"
    description = "Create a timestampable backup copy of a remote file."
    required_params = ("src", "dest")
    optional_params = ("checksum", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.file creates a backup artifact; use manual commands for exact copy and checksum steps"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        src = str(params["src"])
        dest = str(params["dest"])
        sudo = _sudo(params)
        return [
            " && ".join(
                [
                    f"test -f {quote(src)}",
                    f"{sudo}mkdir -p $(dirname {quote(dest)})",
                    f"{sudo}cp -a {quote(src)} {quote(dest)}",
                    _checksum_cmd(dest, params),
                ]
            )
        ]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="backup.file failed")
