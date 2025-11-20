"""
Plugin for checking ICMP connection (ping) utility.
"""

from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    from ping3 import errors, verbose_ping

    PING3_AVAILABLE = True
except ImportError:
    PING3_AVAILABLE = False


@register_plugin
class CheckIcmpConnectionPlugin(BasePlugin):
    """
    Check if a host is reachable via ICMP ping using ping3 library.

    Returns:
        Dictionary containing:
            - status (str): "success" or "failure"
            - host (str): The target hostname or IP address
            - count (int): Number of ping attempts
            - timeout (float): Timeout for each ping attempt
            - interval (float): Interval between pings
            - connected (bool): True if host is reachable
            - success_count (int): Number of successful pings
            - success_rate (float): Percentage of successful pings

    Raises:
        PluginExecutionError: If ping3 library is missing or host resolution fails.

    """

    METADATA = PluginMetadata(
        name="check_icmp_connection",
        version="2.0.0",
        description="Check ICMP connectivity to a host using ping3 library",
        author="Marco Fortina",
        category="network",
        tags=["network", "icmp", "ping", "check"],
        required_config=["host"],
        optional_config=["count", "timeout", "interval", "fail_fast"],
    )

    SCHEMA = {
        "host": {"type": str, "required": True},
        "count": {"type": int, "required": False},
        "timeout": {"type": (int, float), "required": False},
        "interval": {"type": (int, float), "required": False},
        "fail_fast": {"type": bool, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Check ICMP connectivity to host using ping3.

        Returns:
            Dictionary containing:
                - status (str): "success" or "failure"
                - host (str): The target hostname or IP address
                - count (int): Number of ping attempts
                - timeout (float): Timeout for each ping attempt
                - interval (float): Interval between pings
                - connected (bool): True if host is reachable
                - success_count (int): Number of successful pings
                - success_rate (float): Percentage of successful pings
                - error (str): Error message if operation failed

        Raises:
            PluginExecutionError: If ping3 library is missing, host resolution fails,
                                or fail_fast is True and ping fails.

        """
        if not PING3_AVAILABLE:
            raise PluginExecutionError(
                "ping3 library is required for ICMP checks. "
                "Install it with: pip install ping3"
            )

        host = self.config["host"]
        count = self.config.get("count", 4)
        timeout = self.config.get("timeout", 2)
        interval = self.config.get("interval", 0.2)
        fail_fast = self.config.get("fail_fast", True)

        self.logger.info(
            f"Checking ICMP connectivity to {host} with count {count} and timeout {timeout}"
        )

        try:
            success_count = verbose_ping(
                dest_addr=host,
                count=count,
                timeout=timeout,
                interval=interval,
            )

            # Calculate success rate
            success_rate = (success_count / count) * 100 if count > 0 else 0
            success = success_count > 0

            if success:
                self.logger.info(
                    f"ICMP ping to {host} successful ({success_count}/{count} packets received)"
                )
                return {
                    "status": "success",
                    "host": host,
                    "count": count,
                    "timeout": timeout,
                    "interval": interval,
                    "connected": True,
                    "success_count": success_count,
                    "success_rate": success_rate,
                }
            else:
                error_msg = f"ICMP ping to {host} failed (0/{count} packets received)"
                self.logger.error(error_msg)
                if fail_fast:
                    raise PluginExecutionError(error_msg)
                return {
                    "status": "failure",
                    "host": host,
                    "count": count,
                    "timeout": timeout,
                    "interval": interval,
                    "connected": False,
                    "error": error_msg,
                    "success_count": 0,
                    "success_rate": 0.0,
                }

        except errors.HostUnknown as e:
            error_msg = f"Hostname resolution failed for {host}: {e}"
            self.logger.error(error_msg)
            if fail_fast:
                raise PluginExecutionError(error_msg)
            return {
                "status": "failure",
                "host": host,
                "count": count,
                "timeout": timeout,
                "interval": interval,
                "connected": False,
                "error": error_msg,
                "success_count": 0,
                "success_rate": 0.0,
            }

        except Exception as e:
            error_msg = f"ICMP ping check failed: {str(e)}"
            self.logger.error(error_msg)
            if fail_fast:
                raise PluginExecutionError(error_msg)
            return {
                "status": "failure",
                "host": host,
                "count": count,
                "timeout": timeout,
                "interval": interval,
                "connected": False,
                "error": error_msg,
                "success_count": 0,
                "success_rate": 0.0,
            }
