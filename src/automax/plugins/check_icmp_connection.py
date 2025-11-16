"""
Plugin for checking ICMP connection (ping) utility.
"""

from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    from icmplib import exceptions
    from icmplib import ping as icmp_ping

    ICMPLIB_AVAILABLE = True
except ImportError:
    ICMPLIB_AVAILABLE = False


@register_plugin
class CheckIcmpConnectionPlugin(BasePlugin):
    """
    Check if a host is reachable via ICMP ping using pure Python.
    """

    METADATA = PluginMetadata(
        name="check_icmp_connection",
        version="1.0.0",
        description="Check ICMP connectivity to a host using pure Python",
        author="Automax Team",
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
        Check ICMP connectivity to host using pure Python.

        Returns:
            Dictionary containing ping status and details.

        Raises:
            PluginExecutionError: If ping fails and fail_fast is True.

        """
        if not ICMPLIB_AVAILABLE:
            raise PluginExecutionError(
                "icmplib library is required for ICMP checks. "
                "Install it with: pip install icmplib"
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
            # Use icmplib for pure Python ICMP implementation
            result = icmp_ping(
                address=host,
                count=count,
                timeout=timeout,
                interval=interval,
                privileged=False,
            )

            success = result.is_alive
            packet_loss = result.packet_loss
            rtt_avg = result.avg_rtt
            rtt_min = result.min_rtt
            rtt_max = result.max_rtt

            if success:
                self.logger.info(
                    f"ICMP ping to {host} successful (packet loss: {packet_loss}%)"
                )
                return {
                    "status": "success",
                    "host": host,
                    "count": count,
                    "timeout": timeout,
                    "interval": interval,
                    "connected": True,
                    "packet_loss": packet_loss,
                    "rtt_avg_ms": rtt_avg,
                    "rtt_min_ms": rtt_min,
                    "rtt_max_ms": rtt_max,
                    "success_rate": 100 - packet_loss,
                }
            else:
                error_msg = f"ICMP ping to {host} failed (packet loss: {packet_loss}%)"
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
                    "packet_loss": packet_loss,
                    "success_rate": 100 - packet_loss,
                }

        except exceptions.NameLookupError as e:
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
            }
