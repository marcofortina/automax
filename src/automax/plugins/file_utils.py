# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Shared file transfer helpers for SSH-backed plugins.
"""

from __future__ import annotations

from pathlib import Path
import posixpath
import uuid

from automax.core.models import ExecutionContext
from automax.plugins.remote_utils import exec_remote, quote


def remote_dir(path: str) -> str:
    """Return the POSIX parent directory for a remote path."""
    parent = posixpath.dirname(str(path).rstrip("/"))
    return parent or "."


def upload_text_to_temp(context: ExecutionContext, content: str, *, encoding: str = "utf-8") -> str:
    """Upload text content to a remote temporary file and return the remote path."""
    return upload_bytes_to_temp(context, content.encode(encoding), suffix=".txt")


def upload_bytes_to_temp(context: ExecutionContext, content: bytes, *, suffix: str = "") -> str:
    """Upload bytes to a remote temporary file and return the remote path."""
    if context.ssh_client is None:
        raise RuntimeError("file upload requires an SSH session")
    remote_path = f"/tmp/automax-{context.run_id}-{uuid.uuid4().hex}{suffix}"
    sftp = context.ssh_client.open_sftp()
    try:
        with sftp.file(remote_path, "wb") as handle:
            handle.write(content)
    finally:
        sftp.close()
    return remote_path


def remote_remove_tmp(context: ExecutionContext, path: str) -> None:
    """Best-effort removal of a temporary remote file."""
    try:
        exec_remote(context, f"rm -f {quote(path)}")
    except Exception:
        # Cleanup must not hide the primary plugin result.
        return


def install_uploaded_file(
    context: ExecutionContext,
    temp_path: str,
    dest: str,
    *,
    sudo: bool = False,
    mode: str | None = None,
    owner: str | None = None,
    group: str | None = None,
) -> tuple[int, str, str]:
    """Move a remote temp file into final location, preserving idempotent change checks."""
    dest_q = quote(dest)
    temp_q = quote(temp_path)
    mkdir = f"mkdir -p {quote(remote_dir(dest))}"
    install_flags = []
    if mode:
        install_flags.extend(["-m", quote(mode)])
    if owner:
        install_flags.extend(["-o", quote(owner)])
    if group:
        install_flags.extend(["-g", quote(group)])

    if sudo:
        install = " ".join(["sudo -n install", *install_flags, temp_q, dest_q])
        command = (
            f"sudo -n mkdir -p {quote(remote_dir(dest))} && "
            f"if test -e {dest_q} && cmp -s {temp_q} {dest_q}; then "
            f"rm -f {temp_q}; "
            f"else {install} && rm -f {temp_q} && echo __AUTOMAX_CHANGED__; fi"
        )
    else:
        if install_flags:
            install = " ".join(["install", *install_flags, temp_q, dest_q])
            command = (
                f"{mkdir} && "
                f"if test -e {dest_q} && cmp -s {temp_q} {dest_q}; then "
                f"rm -f {temp_q}; "
                f"else {install} && rm -f {temp_q} && echo __AUTOMAX_CHANGED__; fi"
            )
        else:
            command = (
                f"{mkdir} && "
                f"if test -e {dest_q} && cmp -s {temp_q} {dest_q}; then "
                f"rm -f {temp_q}; "
                f"else mv {temp_q} {dest_q} && echo __AUTOMAX_CHANGED__; fi"
            )
    return exec_remote(context, command)


def write_local_file(path: Path, content: bytes) -> None:
    """Write bytes to a local path creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
