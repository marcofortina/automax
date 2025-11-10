"""
Plugin for file uncompression utility (zip and tar.gz).
"""

import tarfile
import zipfile
from pathlib import Path

from automax.core.exceptions import AutomaxError


def uncompress_file(
    source_path: str, dest_dir: str, logger=None, fail_fast=True, dry_run=False
):
    """
    Uncompress a file (zip or tar.gz) to a directory.

    Args:
        source_path (str): Path to compressed file.
        dest_dir (str): Destination directory.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.
        dry_run (bool): If True, simulate uncompression.

    Raises:
        AutomaxError: If fail_fast is True and uncompression fails, with level 'FATAL'.
    """
    from automax.core.utils.common_utils import echo

    source = Path(source_path)

    if dry_run:
        if logger:
            echo(
                f"[DRY-RUN] Uncompress {source_path} to {dest_dir}",
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
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        if source.suffix == ".zip":
            with zipfile.ZipFile(source_path, "r") as zf:
                zf.extractall(dest_dir)
        elif source.suffixes == [".tar", ".gz"]:
            with tarfile.open(source_path, "r:gz") as tf:
                tf.extractall(dest_dir, filter="data")
        else:
            raise ValueError("Unsupported format")
        if logger:
            echo(f"Uncompressed {source_path} to {dest_dir}", logger, level="INFO")
    except Exception as e:
        msg = f"Uncompression failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")


REGISTER_UTILITIES = [("uncompress_file", uncompress_file)]

SCHEMA = {
    "source_path": {"type": str, "required": True},
    "dest_dir": {"type": str, "required": True},
    "fail_fast": {"type": bool, "default": True},
    "dry_run": {"type": bool, "default": False},
}
