"""
Plugin for HTTP request utility.
"""

import json
import urllib.error
import urllib.request

from automax.core.exceptions import AutomaxError


def run_http_request(
    url: str,
    method: str = "GET",
    data: dict = None,
    headers: dict = None,
    logger=None,
    timeout: int = 10,
    fail_fast=True,
    dry_run=False,
):
    """
    Execute an HTTP request (GET or POST).

    Args:
        url (str): URL to request.
        method (str): HTTP method (GET or POST).
        data (dict, optional): Data for POST (JSON).
        headers (dict, optional): Request headers.
        logger (LoggerManager, optional): Logger instance.
        timeout (int): Request timeout in seconds.
        fail_fast (bool): If True, raise AutomaxError on failure.
        dry_run (bool): If True, simulate request.

    Returns:
        str: Response content as string.

    Raises:
        AutomaxError: If fail_fast is True and request fails, with level 'FATAL'.
    """
    from automax.core.utils.common_utils import echo

    if headers is None:
        headers = {}
    if data and method == "POST":
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url, data=data if method == "POST" else None, headers=headers, method=method
    )

    if logger:
        echo(f"HTTP Request: {method} {url}", logger, level="INFO")

    if dry_run:
        if logger:
            echo(f"[DRY-RUN] HTTP {method} to {url}", logger, level="INFO")
        return "Dry-run response"

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as e:
        msg = f"HTTP request failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None


REGISTER_UTILITIES = [("run_http_request", run_http_request)]

SCHEMA = {
    "url": {"type": str, "required": True},
    "method": {"type": str, "default": "GET"},
    "data": {"type": dict, "default": None},
    "headers": {"type": dict, "default": None},
    "timeout": {"type": int, "default": 10},
    "fail_fast": {"type": bool, "default": True},
    "dry_run": {"type": bool, "default": False},
}
