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

class BackupDirectoryPlugin(BasePlugin):
    name = "backup.directory"
    description = "Create a compressed tar backup of a remote directory."
    required_params = ("src", "dest")
    optional_params = ("compression", "checksum", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.directory creates a tar artifact; use manual commands for exact archive and checksum steps"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        src = str(params["src"]).rstrip("/")
        dest = str(params["dest"])
        compression = str(params.get("compression", "gzip"))
        if compression not in {"none", "gzip", "bzip2", "xz"}:
            raise PluginValidationError("compression must be none, gzip, bzip2 or xz")
        flags = {"none": "cf", "gzip": "czf", "bzip2": "cjf", "xz": "cJf"}[compression]
        sudo = _sudo(params)
        return [
            " && ".join(
                [
                    f"test -d {quote(src)}",
                    f"{sudo}mkdir -p $(dirname {quote(dest)})",
                    f"{sudo}tar -{flags} {quote(dest)} -C {quote(str(__import__('pathlib').PurePosixPath(src).parent))} {quote(str(__import__('pathlib').PurePosixPath(src).name))}",
                    _checksum_cmd(dest, params),
                ]
            )
        ]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="backup.directory failed")

class BackupRestorePlugin(BasePlugin):
    name = "backup.restore"
    description = "Restore a remote file or tar archive from an explicit backup artifact."
    required_params = ("src", "dest", "confirm")
    optional_params = ("archive", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if params.get("confirm") is not True:
            raise PluginValidationError("backup.restore requires confirm: true")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.restore is a destructive restore operation guarded by confirm=true"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        src = str(params["src"])
        dest = str(params["dest"])
        sudo = _sudo(params)
        commands = [f"test -e {quote(src)}"]
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(dest)} || {sudo}cp -a {quote(dest)} {quote(dest + str(params.get('backup_suffix', '.pre-restore')))}")
        if bool(params.get("archive", False)):
            commands.extend([f"{sudo}mkdir -p {quote(dest)}", f"{sudo}tar -xf {quote(src)} -C {quote(dest)}"])
        else:
            commands.extend([f"{sudo}mkdir -p $(dirname {quote(dest)})", f"{sudo}cp -a {quote(src)} {quote(dest)}"])
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="backup.restore failed")

class BackupVerifyPlugin(BasePlugin):
    name = "backup.verify"
    description = "Verify a remote backup artifact checksum without changing state."
    required_params = ("path",)
    optional_params = ("checksum_file", "checksum", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.verify is a read-only checksum verification operation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = str(params["path"])
        checksum = str(params.get("checksum", "sha256"))
        if checksum != "sha256":
            raise PluginValidationError("backup.verify supports checksum=sha256")
        checksum_file = str(params.get("checksum_file", path + ".sha256"))
        return [f"cd $(dirname {quote(path)}) && {_sudo(params)}sha256sum -c {quote(checksum_file)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="backup.verify failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
