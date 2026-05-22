"""
Controller-to-target file transfer plugins.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import stat
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file, write_local_file
from automax.plugins.remote_utils import exec_remote, quote


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


def _upload_file(context: ExecutionContext, sftp, src: Path, dest: str) -> None:
    _mkdir_remote(context, _remote_parent(dest))
    sftp.put(str(src), dest)


def _upload_dir(context: ExecutionContext, sftp, src: Path, dest: str) -> None:
    _mkdir_remote(context, dest)
    for item in src.iterdir():
        remote_item = str(PurePosixPath(dest) / item.name)
        if item.is_dir():
            _upload_dir(context, sftp, item, remote_item)
        else:
            _upload_file(context, sftp, item, remote_item)


def _download_file(sftp, src: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    sftp.get(src, str(dest))


def _download_dir(sftp, src: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for entry in sftp.listdir_attr(src):
        remote_item = str(PurePosixPath(src) / entry.filename)
        local_item = dest / entry.filename
        if stat.S_ISDIR(entry.st_mode):
            _download_dir(sftp, remote_item, local_item)
        else:
            _download_file(sftp, remote_item, local_item)


class TransferUploadPlugin(BasePlugin):
    """Upload a file or directory from the controller to a remote target."""

    name = "transfer.upload"
    description = "Upload a local file or directory to a remote target."
    required_params = ("src", "dest")
    optional_params = ("recursive", "sudo", "mode", "owner", "group")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        src = Path(str(params["src"])).expanduser()
        if not src.exists():
            raise PluginValidationError(f"transfer.upload source not found: {src}")
        if src.is_dir() and not bool(params.get("recursive", False)):
            raise PluginValidationError("transfer.upload requires recursive=true for directories")
        if src.is_dir() and bool(params.get("sudo", False)):
            raise PluginValidationError("transfer.upload sudo=true is supported only for files")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        src = Path(str(params["src"])).expanduser()
        dest = str(params["dest"])
        if src.is_file() and bool(params.get("sudo", False)):
            remote_tmp = f"/tmp/automax-upload-{context.run_id}-{src.name}"
            sftp = _sftp(context)
            try:
                sftp.put(str(src), remote_tmp)
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
            if src.is_dir():
                _upload_dir(context, sftp, src, dest)
            else:
                _upload_file(context, sftp, src, dest)
        finally:
            sftp.close()
        return PluginResult.success(changed=True, data={"src": str(src), "dest": dest})


class TransferDownloadPlugin(BasePlugin):
    """Download a file or directory from a remote target to the controller."""

    name = "transfer.download"
    description = "Download a remote file or directory to the controller."
    required_params = ("src", "dest")
    optional_params = ("recursive",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        src = str(params["src"])
        dest = Path(str(params["dest"])).expanduser()
        sftp = _sftp(context)
        try:
            attrs = sftp.stat(src)
            if stat.S_ISDIR(attrs.st_mode):
                if not bool(params.get("recursive", False)):
                    raise PluginValidationError("transfer.download requires recursive=true for directories")
                _download_dir(sftp, src, dest)
            else:
                _download_file(sftp, src, dest)
        finally:
            sftp.close()
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
        src = Path(str(params["src"])).expanduser()
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
        return PluginResult.success(changed=True, data={"src": str(src), "dest": dest})
