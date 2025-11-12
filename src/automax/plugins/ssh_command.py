"""
Plugin for SSH command execution utility.
"""

import subprocess
from pathlib import Path

from automax.core.exceptions import AutomaxError


def run_ssh_command(
    host: str,
    key_path: str,
    command: str,
    logger=None,
    timeout: int = 10,
    fail_fast=True,
    user: str = None,
    port: int = 22,
    dry_run=False,
):
    """
    Execute a command remotely via SSH using a private key.

    Args:
        host (str): Remote host
        key_path (str): Path to private key file
        command (str): Command to execute remotely
        logger (LoggerManager, optional): Logger instance
        timeout (int): SSH command timeout in seconds
        fail_fast (bool): If True, raise AutomaxError on failure
        user (str, optional): SSH username (default None)
        port (int): SSH port (default 22)
        dry_run (bool): If True, simulate execution and do not run real SSH

    Returns:
        subprocess.CompletedProcess: result object with stdout, stderr, returncode

    Raises:
        FileNotFoundError: If private key file not found
        AutomaxError: if fail_fast is True and command fails, with level 'FATAL'

    """
    from automax.core.utils.common_utils import echo

    if not Path(key_path).exists():
        msg = f"Private key not found: {key_path}"
        if logger:
            echo(msg, logger, level="ERROR")
        raise FileNotFoundError(msg)

    ssh_user = f"{user}@" if user else ""
    ssh_cmd = f'ssh -i {key_path} -o StrictHostKeyChecking=no -p {port} {ssh_user}{host} "{command}"'

    if logger:
        echo(f"COMMAND = {ssh_cmd}", logger, level="DEBUG")
        echo(f"Executing SSH command: {ssh_cmd}", logger, level="INFO")

    if dry_run:
        if logger:
            echo(f"[DRY-RUN] SSH to {host}: {command}", logger, level="INFO")
        return subprocess.CompletedProcess(
            args=ssh_cmd, returncode=0, stdout="", stderr=""
        )

    # Execute using subprocess
    try:
        result = subprocess.run(
            ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        msg = f"SSH command timed out: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return subprocess.CompletedProcess(
            args=ssh_cmd, returncode=1, stdout="", stderr=str(e)
        )

    if logger:
        if result.stdout:
            echo(result.stdout.strip(), logger, level="DEBUG")
        if result.stderr:
            echo(result.stderr.strip(), logger, level="ERROR")

    if fail_fast and result.returncode != 0:
        msg = f"SSH command failed with return code {result.returncode}"
        if logger:
            echo(msg, logger, level="ERROR")
        raise AutomaxError(msg, level="FATAL")

    return result


REGISTER_UTILITIES = [("run_ssh_command", run_ssh_command)]

SCHEMA = {
    "host": {"type": str, "required": True},
    "key_path": {"type": str, "required": True},
    "command": {"type": str, "required": True},
    "timeout": {"type": int, "default": 10},
    "fail_fast": {"type": bool, "default": True},
    "user": {"type": str, "default": None},
    "port": {"type": int, "default": 22},
    "dry_run": {"type": bool, "default": False},
}
