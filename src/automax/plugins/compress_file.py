"""
Plugin for file compression utility (zip and tar.gz).
"""

import os
from pathlib import Path
import tarfile
import zipfile

from automax.core.exceptions import AutomaxError


def compress_file(
    source_path: str,
    dest_path: str,
    format: str = "zip",
    logger=None,
    fail_fast=True,
    dry_run=False,
):
    """
    Compress a file or directory (zip or tar.gz).

    Args:
        source_path (str): Path to source file/dir.
        dest_path (str): Path to compressed file.
        format (str): 'zip' or 'tar.gz'.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.
        dry_run (bool): If True, simulate compression.

    Raises:
        AutomaxError: If fail_fast is True and compression fails, with level 'FATAL'.

    """
    from automax.core.utils.common_utils import echo

    source = Path(source_path)

    if dry_run:
        if logger:
            echo(
                f"[DRY-RUN] Compress {source_path} to {dest_path} ({format})",
                logger,
                level="INFO",
            )
        return

    if not source.exists():
        msg = f"Source not found: {source_path}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return

    try:
        if format == "zip":
            with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
                if source.is_file():
                    zf.write(source_path)
                else:
                    for root, _, files in os.walk(source_path):
                        for file in files:
                            zf.write(os.path.join(root, file))
        elif format == "tar.gz":
            with tarfile.open(dest_path, "w:gz") as tf:
                tf.add(source_path)
        else:
            raise ValueError("Unsupported format")
        if logger:
            echo(f"Compressed {source_path} to {dest_path}", logger, level="INFO")
    except Exception as e:
        msg = f"Compression failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")


REGISTER_UTILITIES = [("compress_file", compress_file)]

SCHEMA = {
    "source_path": {"type": str, "required": True},
    "dest_path": {"type": str, "required": True},
    "format": {"type": str, "default": "zip"},
    "fail_fast": {"type": bool, "default": True},
    "dry_run": {"type": bool, "default": False},
}
