"""
Plugin for reading file content utility.
"""

from pathlib import Path

from automax.core.exceptions import AutomaxError


def read_file_content(file_path: str, logger=None, fail_fast=True):
    """
    Read the content of a file.

    Args:
        file_path (str): Path to the file.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        str: File content.

    Raises:
        AutomaxError: If fail_fast is True and reading fails, with level 'FATAL'.

    """
    from automax.core.utils.common_utils import echo

    path = Path(file_path)
    if not path.exists():
        msg = f"File not found: {file_path}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None

    try:
        content = path.read_text()
        if logger:
            echo(f"Read file: {file_path}", logger, level="INFO")
        return content
    except Exception as e:
        msg = f"Failed to read file: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None


REGISTER_UTILITIES = [("read_file_content", read_file_content)]

SCHEMA = {
    "file_path": {"type": str, "required": True},
    "fail_fast": {"type": bool, "default": True},
}
