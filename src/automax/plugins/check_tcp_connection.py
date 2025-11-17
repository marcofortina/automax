"""
Plugin for checking TCP connectivity.
"""

import socket
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class CheckTCPConnectionPlugin(BasePlugin):
    """
    Check if a TCP connection to host:port is reachable.
    """

    METADATA = PluginMetadata(
        name="check_tcp_connection",
        version="2.0.0",
        description="Check TCP connectivity to a host and port",
        author="Automax Team",
        category="network",
        tags=["network", "tcp", "connection"],
        required_config=["host", "port"],
        optional_config=["timeout", "fail_fast"],
    )

    SCHEMA = {
        "host": {"type": str, "required": True},
        "port": {"type": int, "required": True},
        "timeout": {"type": (int, float), "required": False},
        "fail_fast": {"type": bool, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Attempt a TCP connection to the specified host and port.

        Returns:
            dict: host, port, timeout, connected (bool), status, error (if any)

        Raises:
            PluginExecutionError: if fail_fast is True and connection fails

        """
        host = self.config["host"]
        port = self.config["port"]
        timeout = self.config.get("timeout", 5)
        fail_fast = self.config.get("fail_fast", True)

        self.logger.info(
            f"Checking TCP connection to {host}:{port} (timeout={timeout})"
        )

        try:
            with socket.create_connection((host, port), timeout=timeout):
                self.logger.info(f"TCP connection to {host}:{port} successful")
                return {
                    "status": "success",
                    "host": host,
                    "port": port,
                    "timeout": timeout,
                    "connected": True,
                }
        except Exception as e:
            error_msg = f"TCP connection to {host}:{port} failed: {e}"
            self.logger.error(error_msg)
            if fail_fast:
                raise PluginExecutionError(error_msg)
            return {
                "status": "failure",
                "host": host,
                "port": port,
                "timeout": timeout,
                "connected": False,
                "error": str(e),
            }
