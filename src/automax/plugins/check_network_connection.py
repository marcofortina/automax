"""
Plugin for checking network connection utility.
"""

import socket

from automax.core.exceptions import AutomaxError


def check_network_connection(
    host: str, port: int = 80, timeout: int = 5, logger=None, fail_fast=True
):
    """
    Check if a network connection to host:port is possible.

    Args:
        host (str): Host to check.
        port (int): Port to check (default 80).
        timeout (int): Connection timeout.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        bool: True if connected, False otherwise.

    Raises:
        AutomaxError: If fail_fast is True and check fails, with level 'FATAL'.

    """
    from automax.core.utils.common_utils import echo

    try:
        with socket.create_connection((host, port), timeout=timeout):
            if logger:
                echo(f"Connection to {host}:{port} successful", logger, level="INFO")
            return True
    except Exception as e:
        msg = f"Connection to {host}:{port} failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return False


REGISTER_UTILITIES = [("check_network_connection", check_network_connection)]

SCHEMA = {
    "host": {"type": str, "required": True},
    "port": {"type": int, "default": 80},
    "timeout": {"type": int, "default": 5},
    "fail_fast": {"type": bool, "default": True},
}
