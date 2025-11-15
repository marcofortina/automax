"""
Plugin for checking network connection utility.
"""

import socket
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class CheckNetworkConnectionPlugin(BasePlugin):
    """
    Check if a network connection to host:port is possible.
    """

    METADATA = PluginMetadata(
        name="check_network_connection",
        version="2.0.0",
        description="Check network connection to a host and port",
        author="Automax Team",
        category="network",
        tags=["network", "connection", "check"],
        required_config=["host"],
        optional_config=["port", "timeout", "fail_fast"],
    )

    SCHEMA = {
        "host": {"type": str, "required": True},
        "port": {"type": int, "required": True},
        "timeout": {"type": (int, float), "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Check network connection to host:port.

        Returns:
            Dictionary containing connection status and details.

        Raises:
            PluginExecutionError: If connection fails and fail_fast is True.

        """
        host = self.config["host"]
        port = self.config.get("port", 80)
        timeout = self.config.get("timeout", 5)
        fail_fast = self.config.get("fail_fast", True)

        self.logger.info(f"Checking connection to {host}:{port} with timeout {timeout}")

        try:
            with socket.create_connection((host, port), timeout=timeout):
                self.logger.info(f"Connection to {host}:{port} successful")
                return {
                    "status": "success",
                    "host": host,
                    "port": port,
                    "timeout": timeout,
                    "connected": True,
                }
        except Exception as e:
            error_msg = f"Connection to {host}:{port} failed: {e}"
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
