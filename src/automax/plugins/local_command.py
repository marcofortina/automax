"""
Plugin for local command execution utility.
"""

import subprocess

from automax.core.exceptions import AutomaxError


def run_local_command(command: str, logger=None, fail_fast=True, dry_run=False):
    """
    Execute a local OS command, log output and optionally fail fast.

    Args:
        command (str): Command to execute
        logger (LoggerManager, optional): Logger instance
        fail_fast (bool): If True, raise AutomaxError on non-zero return code
        dry_run (bool): If True, do not execute command (simulate)

    Returns:
        subprocess.CompletedProcess: result object with stdout, stderr, returncode

    Raises:
        AutomaxError: if fail_fast is True and command fails, with level 'FATAL'
    """
    from automax.core.utils.common_utils import echo

    if logger:
        echo(f"COMMAND = {command}", logger, level="DEBUG")
        echo(f"Executing local command: {command}", logger, level="INFO")

    if dry_run:
        if logger:
            echo(f"[DRY-RUN] {command}", logger, level="INFO")
        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout="", stderr=""
        )

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if logger:
        if result.stdout:
            echo(result.stdout.strip(), logger, level="DEBUG")
        if result.stderr:
            echo(result.stderr.strip(), logger, level="ERROR")

    if fail_fast and result.returncode != 0:
        msg = f"Command failed with return code {result.returncode}"
        if logger:
            echo(msg, logger, level="ERROR")
        raise AutomaxError(msg, level="FATAL")

    return result


REGISTER_UTILITIES = [("run_local_command", run_local_command)]

SCHEMA = {
    "command": {"type": str, "required": True},
    "fail_fast": {"type": bool, "default": True},
    "dry_run": {"type": bool, "default": False},
}
