# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Controller-to-target file transfer plugins.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import subprocess
import hashlib
import os
import stat
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file
from automax.plugins.remote_utils import exec_remote, quote


def _is_templated_path(value: str) -> bool:
    """Return true when validation must wait until job rendering."""
    return "{{" in value or "{%" in value or "{#" in value


def _sftp(context: ExecutionContext):
    if context.ssh_client is None:
        raise RuntimeError("transfer plugin requires an SSH session")
    return context.ssh_client.open_sftp()


def _remote_parent(path: str) -> str:
    parent = str(PurePosixPath(path).parent)
    return parent if parent != "." else "."


def _mkdir_remote(context: ExecutionContext, path: str) -> None:
    if not path or path == ".":
        return
    exec_remote(context, f"mkdir -p {quote(path)}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_checksum(path: Path, expected: str) -> None:
    actual = _sha256_file(path)
    if actual.lower() != str(expected).lower():
        raise PluginValidationError(f"checksum mismatch for {path}: expected {expected}, got {actual}")


def _remote_backup_command(path: str, suffix: str) -> str:
    return f"test ! -e {quote(path)} || cp -a {quote(path)} {quote(path + suffix)}"


def _remote_exists(context: ExecutionContext, path: str) -> bool:
    rc, _, _ = exec_remote(context, f"test -e {quote(path)}")
    return rc == 0


def _remote_safe_prepare(context: ExecutionContext, dest: str, params: Dict[str, Any]) -> None:
    if bool(params.get("backup_existing", False)):
        exec_remote(context, _remote_backup_command(dest, str(params.get("backup_suffix", ".bak"))))
    if not bool(params.get("overwrite", True)) and _remote_exists(context, dest):
        raise PluginValidationError(f"destination already exists: {dest}")


def _remote_apply_attrs(context: ExecutionContext, path: str, params: Dict[str, Any], *, recursive: bool = False) -> None:
    commands = []
    recurse = " -R" if recursive else ""
    if params.get("mode"):
        commands.append(f"chmod{recurse} {quote(params['mode'])} {quote(path)}")
    if params.get("owner") or params.get("group"):
        spec = f"{params.get('owner', '')}:{params.get('group', '')}"
        commands.append(f"chown{recurse} {quote(spec)} {quote(path)}")
    if commands:
        exec_remote(context, " && ".join(commands))


def _upload_file(context: ExecutionContext, sftp, src: Path, dest: str, *, preserve_times: bool = False) -> None:
    _mkdir_remote(context, _remote_parent(dest))
    sftp.put(str(src), dest)
    if preserve_times:
        stat_result = src.stat()
        sftp.utime(dest, (stat_result.st_atime, stat_result.st_mtime))


def _upload_dir(context: ExecutionContext, sftp, src: Path, dest: str, *, preserve_times: bool = False) -> None:
    _mkdir_remote(context, dest)
    for item in src.iterdir():
        remote_item = str(PurePosixPath(dest) / item.name)
        if item.is_dir():
            _upload_dir(context, sftp, item, remote_item, preserve_times=preserve_times)
        else:
            _upload_file(context, sftp, item, remote_item, preserve_times=preserve_times)
    if preserve_times:
        stat_result = src.stat()
        sftp.utime(dest, (stat_result.st_atime, stat_result.st_mtime))


def _download_file(sftp, src: str, dest: Path, *, preserve_times: bool = False) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    attrs = sftp.stat(src)
    sftp.get(src, str(dest))
    if preserve_times:
        os.utime(dest, (attrs.st_atime, attrs.st_mtime))


def _download_dir(sftp, src: str, dest: Path, *, preserve_times: bool = False) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    attrs = sftp.stat(src)
    for entry in sftp.listdir_attr(src):
        remote_item = str(PurePosixPath(src) / entry.filename)
        local_item = dest / entry.filename
        if stat.S_ISDIR(entry.st_mode):
            _download_dir(sftp, remote_item, local_item, preserve_times=preserve_times)
        else:
            _download_file(sftp, remote_item, local_item, preserve_times=preserve_times)
    if preserve_times:
        os.utime(dest, (attrs.st_atime, attrs.st_mtime))


class TransferUploadPlugin(BasePlugin):
    """Upload a file or directory from the controller to a remote target."""

    name = "transfer.upload"
    description = "Upload a local file or directory to a remote target."
    required_params = ("src", "dest")
    optional_params = ("recursive", "sudo", "mode", "owner", "group", "checksum", "overwrite", "backup_existing", "backup_suffix", "preserve_times")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        src_value = str(params["src"])
        if _is_templated_path(src_value):
            return
        src = Path(src_value).expanduser()
        if not src.exists():
            raise PluginValidationError(f"transfer.upload source not found: {src}")
        if src.is_dir() and not bool(params.get("recursive", False)):
            raise PluginValidationError("transfer.upload requires recursive=true for directories")
        if src.is_dir() and bool(params.get("sudo", False)):
            raise PluginValidationError("transfer.upload sudo=true is supported only for files")
        if params.get("checksum") and src.is_dir():
            raise PluginValidationError("transfer.upload checksum is supported only for files")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        src = Path(str(params["src"])).expanduser()
        dest = str(params["dest"])
        if params.get("checksum"):
            _assert_checksum(src, str(params["checksum"]))
        if src.is_file() and bool(params.get("sudo", False)):
            _remote_safe_prepare(context, dest, params)
            remote_tmp = f"/tmp/automax-upload-{context.run_id}-{src.name}"
            sftp = _sftp(context)
            try:
                sftp.put(str(src), remote_tmp)
                if bool(params.get("preserve_times", False)):
                    stat_result = src.stat()
                    sftp.utime(remote_tmp, (stat_result.st_atime, stat_result.st_mtime))
            finally:
                sftp.close()
            rc, out, err = install_uploaded_file(
                context,
                remote_tmp,
                dest,
                sudo=True,
                mode=params.get("mode"),
                owner=params.get("owner"),
                group=params.get("group"),
            )
            if rc != 0:
                return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="transfer.upload failed")
            changed = "__AUTOMAX_CHANGED__" in out
            return PluginResult.success(changed=changed, stdout=out.replace("__AUTOMAX_CHANGED__", "").strip(), data={"src": str(src), "dest": dest})

        sftp = _sftp(context)
        try:
            _remote_safe_prepare(context, dest, params)
            if src.is_dir():
                _upload_dir(context, sftp, src, dest, preserve_times=bool(params.get("preserve_times", False)))
            else:
                _upload_file(context, sftp, src, dest, preserve_times=bool(params.get("preserve_times", False)))
        finally:
            sftp.close()
        if params.get("checksum"):
            exec_remote(context, f"sha256sum {quote(dest)} | awk '{{print $1}}' | grep -Fx -- {quote(params['checksum'])}")
        _remote_apply_attrs(context, dest, params, recursive=src.is_dir())
        return PluginResult.success(changed=True, data={"src": str(src), "dest": dest})


class TransferDownloadPlugin(BasePlugin):
    """Download a file or directory from a remote target to the controller."""

    name = "transfer.download"
    description = "Download a remote file or directory to the controller."
    required_params = ("src", "dest")
    optional_params = ("recursive", "checksum", "overwrite", "backup_existing", "backup_suffix", "mode", "owner", "group", "preserve_times")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        src = str(params["src"])
        dest = Path(str(params["dest"])).expanduser()
        if dest.exists():
            if bool(params.get("backup_existing", False)):
                backup_dest = dest.with_name(dest.name + str(params.get("backup_suffix", ".bak")))
                if dest.is_dir():
                    import shutil
                    if backup_dest.exists():
                        shutil.rmtree(backup_dest)
                    shutil.copytree(dest, backup_dest)
                else:
                    backup_dest.write_bytes(dest.read_bytes())
            if not bool(params.get("overwrite", True)):
                raise PluginValidationError(f"destination already exists: {dest}")
        sftp = _sftp(context)
        try:
            attrs = sftp.stat(src)
            if stat.S_ISDIR(attrs.st_mode):
                if not bool(params.get("recursive", False)):
                    raise PluginValidationError("transfer.download requires recursive=true for directories")
                _download_dir(sftp, src, dest, preserve_times=bool(params.get("preserve_times", False)))
            else:
                _download_file(sftp, src, dest, preserve_times=bool(params.get("preserve_times", False)))
        finally:
            sftp.close()
        if params.get("checksum"):
            _assert_checksum(dest, str(params["checksum"]))
        if params.get("mode"):
            dest.chmod(int(str(params["mode"]), 8))
        return PluginResult.success(changed=True, data={"src": src, "dest": str(dest)})


class TransferSyncPlugin(BasePlugin):
    """Upload a local directory tree to a remote directory."""

    name = "transfer.sync"
    description = "Sync a local directory tree to a remote directory."
    required_params = ("src", "dest")
    optional_params = ()
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        src_value = str(params["src"])
        if _is_templated_path(src_value):
            return
        src = Path(src_value).expanduser()
        if not src.is_dir():
            raise PluginValidationError("transfer.sync source must be a directory")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        src = Path(str(params["src"])).expanduser()
        dest = str(params["dest"])
        sftp = _sftp(context)
        try:
            _upload_dir(context, sftp, src, dest)
        finally:
            sftp.close()
        if params.get("checksum"):
            exec_remote(context, f"sha256sum {quote(dest)} | awk '{{print $1}}' | grep -Fx -- {quote(params['checksum'])}")
        _remote_apply_attrs(context, dest, params, recursive=src.is_dir())
        return PluginResult.success(changed=True, data={"src": str(src), "dest": dest})


class TransferRsyncPlugin(BasePlugin):
    """Synchronize files using the local rsync executable."""

    name = "transfer.rsync"
    description = "Synchronize files with rsync using the current target as the default remote endpoint."
    required_params = ("src", "dest")
    optional_params = ("direction", "archive", "compress", "delete", "checksum", "dry_run", "excludes", "ssh_options", "rsync_path", "timeout")
    parameter_schema = {"archive": {"type": "boolean", "default": True, "description": "Use rsync archive mode."}}
    opens_remote_session = False
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        direction = str(params.get("direction", "upload"))
        if direction not in {"upload", "download", "local"}:
            raise PluginValidationError("transfer.rsync direction must be upload, download or local")

    def _target_prefix(self, context: ExecutionContext) -> str:
        user = f"{context.target.user}@" if context.target.user else ""
        return f"{user}{context.target.host}:"

    def _remote_path(self, value: str, context: ExecutionContext) -> str:
        if ":" in value or str(value).startswith("/") and str(value).startswith("//"):
            return value
        return self._target_prefix(context) + value

    def _command_parts(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        parts = ["rsync"]
        parts.append("-a" if bool(params.get("archive", True)) else "-r")
        if bool(params.get("compress", False)):
            parts.append("-z")
        if bool(params.get("delete", False)):
            parts.append("--delete")
        if bool(params.get("checksum", False)):
            parts.append("--checksum")
        if bool(params.get("dry_run", False)) or context.dry_run:
            parts.append("--dry-run")
        if params.get("rsync_path"):
            parts.extend(["--rsync-path", str(params["rsync_path"])])
        ssh_options = params.get("ssh_options")
        if ssh_options:
            if isinstance(ssh_options, list):
                ssh_options = " ".join(str(item) for item in ssh_options)
            parts.extend(["-e", f"ssh {ssh_options}"])
        excludes = params.get("excludes") or []
        if isinstance(excludes, str):
            excludes = [excludes]
        for pattern in excludes:
            parts.extend(["--exclude", str(pattern)])
        direction = str(params.get("direction", "upload"))
        src = str(params["src"])
        dest = str(params["dest"])
        if direction == "upload":
            parts.extend([src, self._remote_path(dest, context)])
        elif direction == "download":
            parts.extend([self._remote_path(src, context), dest])
        else:
            parts.extend([src, dest])
        return parts

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "transfer.rsync previews changes with rsync --dry-run rather than a deterministic file diff"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [" ".join(quote(part) for part in self._command_parts(params, context))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = self._command_parts(params, context)
        completed = subprocess.run(command, text=True, capture_output=True, timeout=float(params.get("timeout", 0)) or None, check=False)
        if completed.returncode != 0:
            return PluginResult.failure(rc=completed.returncode, stdout=completed.stdout, stderr=completed.stderr, message="transfer.rsync failed")
        changed = bool(completed.stdout.strip()) and not (bool(params.get("dry_run", False)) or context.dry_run)
        return PluginResult.success(changed=changed, rc=completed.returncode, stdout=completed.stdout, stderr=completed.stderr, data={"command": command})

# Extended rsync operator controls.

def _rsync_parts_extended(self: TransferRsyncPlugin, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
    parts = TransferRsyncPlugin._command_parts(self, params, context)
    insert_at = 1
    extras: list[str] = []
    if bool(params.get("partial", False)):
        extras.append("--partial")
    if params.get("bwlimit") is not None:
        extras.extend(["--bwlimit", str(params["bwlimit"])])
    if bool(params.get("numeric_ids", False)):
        extras.append("--numeric-ids")
    if bool(params.get("itemize_changes", False)):
        extras.append("--itemize-changes")
    if bool(params.get("stats", False)):
        extras.append("--stats")
    return parts[:insert_at] + extras + parts[insert_at:]


class ExtendedTransferRsyncPlugin(TransferRsyncPlugin):
    """transfer.rsync with extended operator controls."""

    optional_params = ("direction", "archive", "compress", "delete", "checksum", "dry_run", "excludes", "ssh_options", "rsync_path", "timeout", "partial", "bwlimit", "numeric_ids", "itemize_changes", "stats")

    def _command_parts(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return _rsync_parts_extended(self, params, context)
