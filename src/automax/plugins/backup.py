# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Operational backup and restore plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix


def _sudo(params: Dict[str, Any]) -> str:
    return sudo_prefix(params, default=True)


def _checksum_cmd(path: str, params: Dict[str, Any]) -> str:
    checksum = str(params.get("checksum", "sha256"))
    if checksum == "none":
        return "true"
    if checksum != "sha256":
        raise PluginValidationError("checksum must be sha256 or none")
    if bool(params.get("sudo", True)):
        return f"sudo -n sha256sum {quote(path)} | sudo -n tee {quote(path + '.sha256')} >/dev/null"
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
    parameter_schema = {
        "archive": {
            "type": "boolean",
            "description": "Treat the source as an archive artifact.",
        }
    }
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
            commands.append(f"if test -e {quote(dest)}; then {sudo}cp -a {quote(dest)} {quote(dest + str(params.get('backup_suffix', '.pre-restore')))}; fi")
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


def _patterns_expr(patterns: Any) -> str:
    items = patterns if isinstance(patterns, list) else [patterns]
    if not items or items == [None]:
        items = ["*"]
    expr = " -o ".join(f"-name {quote(str(item))}" for item in items)
    return f"\\( {expr} \\)"


class BackupManifestPlugin(BasePlugin):
    name = "backup.manifest"
    description = "Create or print a deterministic manifest for a backup directory or selected paths."
    required_params = ("root",)
    optional_params = ("dest", "paths", "content_checksums", "checksum", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.manifest records backup inventory metadata and optional file checksums"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        root = str(params["root"])
        sudo = _sudo(params)
        output = params.get("dest")
        paths = params.get("paths") or ["."]
        if isinstance(paths, str):
            paths = [paths]
        find_paths = " ".join(quote(str(item)) for item in paths)
        checksum_command = ""
        if bool(params.get("content_checksums", True)):
            checksum_tool = f"{sudo}sha256sum"
            checksum_command = f" | while IFS= read -r file; do {checksum_tool} \"$file\"; done"
        manifest_cmd = (
            f"cd {quote(root)} && "
            f"find {find_paths} -type f -print | LC_ALL=C sort{checksum_command}"
        )
        if output:
            commands = [
                f"{sudo}mkdir -p $(dirname {quote(output)})",
                f"{manifest_cmd} | {sudo}tee {quote(output)} >/dev/null",
            ]
            if str(params.get("checksum", "sha256")) == "sha256":
                commands.append(_checksum_cmd(str(output), params))
            return [" && ".join(commands)]
        return [manifest_cmd]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = self.manual_commands(params, context)[0]
        rc, out, err = exec_remote(context, command + (f" && echo {CHANGE_MARKER}" if params.get("dest") else ""))
        if params.get("dest"):
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="backup.manifest failed")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="backup.manifest failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"manifest": out})


class BackupPrunePlugin(BasePlugin):
    name = "backup.prune"
    description = "Prune backup artifacts by age and/or retention count."
    required_params = ("path",)
    optional_params = ("patterns", "older_than_days", "keep", "confirm", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if params.get("confirm") is not True:
            raise PluginValidationError("backup.prune requires confirm: true")
        if params.get("older_than_days") is None and params.get("keep") is None:
            raise PluginValidationError("backup.prune requires older_than_days and/or keep")
        if params.get("keep") is not None and int(params["keep"]) < 0:
            raise PluginValidationError("backup.prune keep must be >= 0")
        if params.get("older_than_days") is not None and int(params["older_than_days"]) < 0:
            raise PluginValidationError("backup.prune older_than_days must be >= 0")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.prune deletes old backup artifacts and is guarded by confirm=true"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        path = quote(params["path"])
        patterns = _patterns_expr(params.get("patterns"))
        commands = [f"test -d {path}"]
        if params.get("older_than_days") is not None:
            commands.append(
                f"{sudo}find {path} -maxdepth 1 -type f {patterns} -mtime +{quote(params['older_than_days'])} -print -delete"
            )
        if params.get("keep") is not None:
            script = r'''
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
keep = int(sys.argv[2])
patterns = sys.argv[3:]
files = []
for pattern in patterns or ["*"]:
    files.extend(item for item in root.glob(pattern) if item.is_file())
for item in sorted(set(files), key=lambda p: p.stat().st_mtime, reverse=True)[keep:]:
    print(item)
    item.unlink()
'''
            pattern_args = params.get("patterns") or ["*"]
            if isinstance(pattern_args, str):
                pattern_args = [pattern_args]
            commands.append(
                f"{sudo}python3 - {path} {quote(params['keep'])} "
                + " ".join(quote(item) for item in pattern_args)
                + f" <<'PY'\n{script}\nPY"
            )
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="backup.prune failed")


class BackupRotatePlugin(BasePlugin):
    name = "backup.rotate"
    description = "Rotate one backup artifact through numbered generations."
    required_params = ("path", "keep")
    optional_params = ("confirm", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if params.get("confirm") is not True:
            raise PluginValidationError("backup.rotate requires confirm: true")
        if int(params["keep"]) < 1:
            raise PluginValidationError("backup.rotate keep must be >= 1")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.rotate renames backup generations and is guarded by confirm=true"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        path = str(params["path"])
        keep = int(params["keep"])
        commands = [f"{sudo}rm -f -- {quote(path + '.' + str(keep))}"]
        for index in range(keep - 1, 0, -1):
            src = f"{path}.{index}"
            dest = f"{path}.{index + 1}"
            commands.append(f"test ! -e {quote(src)} || {sudo}mv -- {quote(src)} {quote(dest)}")
        commands.append(f"test ! -e {quote(path)} || {sudo}mv -- {quote(path)} {quote(path + '.1')}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="backup.rotate failed")


class BackupRestorePreviewPlugin(BasePlugin):
    name = "backup.restore_preview"
    description = "Preview a restore artifact without changing the target."
    required_params = ("src", "dest")
    optional_params = ("archive", "checksum_file", "checksum", "sudo")
    parameter_schema = {
        "archive": {
            "type": "boolean",
            "description": "Treat the source as an archive artifact.",
        }
    }
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.restore_preview is a read-only restore plan and artifact inspection"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        src = str(params["src"])
        dest = str(params["dest"])
        commands = [f"test -e {quote(src)}"]
        if params.get("checksum_file"):
            commands.append(f"cd $(dirname {quote(src)}) && {_sudo(params)}sha256sum -c {quote(params['checksum_file'])}")
        if bool(params.get("archive", False)):
            commands.append(f"{_sudo(params)}tar -tf {quote(src)} | sed 's#^#{dest.rstrip('/')}/#'")
        else:
            commands.append(f"printf '%s -> %s\\n' {quote(src)} {quote(dest)}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="backup.restore_preview failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"preview": out})


class BackupRestoreVerifyPlugin(BasePlugin):
    name = "backup.restore_verify"
    description = "Verify that restored content matches a backup artifact."
    required_params = ("src", "dest")
    optional_params = ("archive", "checksum_file", "checksum", "sudo")
    parameter_schema = {
        "archive": {
            "type": "boolean",
            "description": "Treat the source as an archive artifact.",
        }
    }
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "backup.restore_verify is a read-only restore verification"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        src = str(params["src"])
        dest = str(params["dest"])
        commands = [f"test -e {quote(src)}", f"test -e {quote(dest)}"]
        if params.get("checksum_file"):
            commands.append(f"cd $(dirname {quote(src)}) && {_sudo(params)}sha256sum -c {quote(params['checksum_file'])}")
        if bool(params.get("archive", False)):
            commands.append(f"{_sudo(params)}tar -df {quote(src)} -C {quote(dest)}")
        else:
            commands.append(f"cmp -s -- {quote(src)} {quote(dest)}")
        return [" && ".join(commands)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="backup.restore_verify failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
