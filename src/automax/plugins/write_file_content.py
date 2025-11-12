"""
Plugin for writing file content utility.
"""

from pathlib import Path

from automax.core.exceptions import AutomaxError


def write_file_content(
    file_path: str, content: str, logger=None, fail_fast=True, dry_run=False
):
    """
    Write content to a file.

    Args:
        file_path (str): Path to the file.
        content (str): Content to write.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.
        dry_run (bool): If True, simulate writing.

    Raises:
        AutomaxError: If fail_fast is True and writing fails, with level 'FATAL'.

    """
    from automax.core.utils.common_utils import echo

    if dry_run:
        if logger:
            echo(f"[DRY-RUN] Write to {file_path}", logger, level="INFO")
        return

    path = Path(file_path)
    try:
        path.write_text(content)
        if logger:
            echo(f"Wrote file: {file_path}", logger, level="INFO")
    except Exception as e:
        msg = f"Failed to write file: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")


REGISTER_UTILITIES = [("write_file_content", write_file_content)]

SCHEMA = {
    "file_path": {"type": str, "required": True},
    "content": {"type": str, "required": True},
    "fail_fast": {"type": bool, "default": True},
    "dry_run": {"type": bool, "default": False},
}
