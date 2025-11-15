"""
Plugin for retrieving secrets from HashiCorp Vault.
"""

from typing import Any, Dict

import requests

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class HashicorpVaultPlugin(BasePlugin):
    """
    Retrieve secrets from HashiCorp Vault.
    """

    METADATA = PluginMetadata(
        name="hashicorp_vault",
        version="2.0.0",
        description="Retrieve secrets from HashiCorp Vault",
        author="Automax Team",
        category="cloud",
        tags=["vault", "secrets", "hashicorp"],
        required_config=["vault_url", "secret_path"],
        optional_config=["token", "engine", "timeout"],
    )

    SCHEMA = {
        "vault_url": {"type": str, "required": True},
        "secret_path": {"type": str, "required": True},
        "token": {"type": str, "required": False},
        "engine": {"type": str, "required": False},
        "timeout": {"type": (int, float), "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Retrieve a secret from HashiCorp Vault.

        Returns:
            Dictionary containing the secret value and metadata.

        Raises:
            PluginExecutionError: If the secret cannot be retrieved.

        """
        vault_url = self.config["vault_url"]
        secret_path = self.config["secret_path"]
        token = self.config.get("token")
        engine = self.config.get("engine", "secret")
        timeout = self.config.get("timeout", 30)

        self.logger.info(f"Retrieving secret: {secret_path} from Vault: {vault_url}")

        if not token:
            raise PluginExecutionError("Vault token is required")

        try:
            headers = {"X-Vault-Token": token}
            url = f"{vault_url}/v1/{engine}/data/{secret_path}"

            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            secret_data = data.get("data", {}).get("data", {})

            result = {
                "vault_url": vault_url,
                "secret_path": secret_path,
                "engine": engine,
                "secret_data": secret_data,
                "status": "success",
            }

            self.logger.info(f"Successfully retrieved secret: {secret_path}")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Vault request failed: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to retrieve secret {secret_path} from Vault: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
