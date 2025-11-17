"""
Plugin for making HTTP requests.
"""

from typing import Any, Dict

import requests
from requests.auth import HTTPBasicAuth

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class RunHttpRequestPlugin(BasePlugin):
    """
    Make HTTP requests to APIs with optional Basic Auth.
    """

    METADATA = PluginMetadata(
        name="run_http_request",
        version="2.0.0",
        description="Make HTTP requests to APIs with optional Basic Auth",
        author="Automax Team",
        category="communication",
        tags=["http", "api", "request"],
        required_config=["url"],
        optional_config=[
            "method",
            "headers",
            "data",
            "params",
            "timeout",
            "verify_ssl",
            "auth_username",
            "auth_password",
        ],
    )

    SCHEMA = {
        "url": {"type": str, "required": True},
        "method": {"type": str, "required": False},
        "headers": {"type": dict, "required": False},
        "data": {"type": (dict, str), "required": False},
        "params": {"type": dict, "required": False},
        "timeout": {"type": (int, float), "required": False},
        "verify_ssl": {"type": bool, "required": False},
        "auth_username": {"type": str, "required": False},
        "auth_password": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Make an HTTP request.

        Returns:
            Dictionary containing the response data.

        Raises:
            PluginExecutionError: If the request fails.

        """
        url = self.config["url"]
        method = self.config.get("method", "GET").upper()
        headers = self.config.get("headers", {})
        data = self.config.get("data")
        params = self.config.get("params", {})
        timeout = self.config.get("timeout", 30)
        verify_ssl = self.config.get("verify_ssl", True)
        auth_username = self.config.get("auth_username")
        auth_password = self.config.get("auth_password")

        self.logger.info(f"Making {method} request to: {url}")

        try:
            auth = (
                HTTPBasicAuth(auth_username, auth_password)
                if auth_username and auth_password
                else None
            )

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                timeout=timeout,
                verify=verify_ssl,
                auth=auth,
            )

            result = {
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "elapsed": response.elapsed.total_seconds(),
                "status": "success" if response.status_code < 400 else "failure",
            }

            self.logger.info(
                f"HTTP request completed with status: {response.status_code}"
            )
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during HTTP request: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
