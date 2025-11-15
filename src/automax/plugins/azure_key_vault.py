"""
Plugin for retrieving secrets from Azure Key Vault.
"""

from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


@register_plugin
class AzureKeyVaultPlugin(BasePlugin):
    """
    Retrieve secrets from Azure Key Vault.
    """

    METADATA = PluginMetadata(
        name="azure_key_vault",
        version="2.0.0",
        description="Retrieve secrets from Azure Key Vault",
        author="Automax Team",
        category="cloud",
        tags=["azure", "secrets", "cloud"],
        required_config=["vault_url", "secret_name"],
        optional_config=["tenant_id", "client_id", "client_secret"],
    )

    SCHEMA = {
        "vault_url": {"type": str, "required": True},
        "secret_name": {"type": str, "required": True},
        "tenant_id": {"type": str, "required": False},
        "client_id": {"type": str, "required": False},
        "client_secret": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Retrieve a secret from Azure Key Vault.

        Returns:
            Dictionary containing the secret value and metadata.

        Raises:
            PluginExecutionError: If the secret cannot be retrieved.

        """
        if not AZURE_AVAILABLE:
            raise PluginExecutionError(
                "Azure SDK not installed. Install with: pip install azure-identity azure-keyvault-secrets"
            )

        vault_url = self.config["vault_url"]
        secret_name = self.config["secret_name"]
        tenant_id = self.config.get("tenant_id")
        client_id = self.config.get("client_id")
        client_secret = self.config.get("client_secret")

        self.logger.info(f"Retrieving secret: {secret_name} from vault: {vault_url}")

        try:
            credential = self._get_credential(tenant_id, client_id, client_secret)
            client = SecretClient(vault_url=vault_url, credential=credential)
            secret = client.get_secret(secret_name)

            result = {
                "vault_url": vault_url,
                "secret_name": secret_name,
                "secret_value": secret.value,
                "version": secret.properties.version,
                "enabled": secret.properties.enabled,
                "expires_on": (
                    secret.properties.expires_on.isoformat()
                    if secret.properties.expires_on
                    else None
                ),
                "status": "success",
            }

            self.logger.info(f"Successfully retrieved secret: {secret_name}")
            return result

        except Exception as e:
            error_msg = (
                f"Failed to retrieve secret {secret_name} from Azure Key Vault: {e}"
            )
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

    def _get_credential(
        self, tenant_id: str = None, client_id: str = None, client_secret: str = None
    ):
        """
        Get Azure credential using various authentication methods.
        """
        try:
            if tenant_id and client_id and client_secret:
                from azure.identity import ClientSecretCredential

                return ClientSecretCredential(tenant_id, client_id, client_secret)
            else:
                return DefaultAzureCredential()
        except Exception as e:
            self.logger.error(f"Failed to get Azure credential: {e}")
            raise PluginExecutionError(f"Failed to get Azure credential: {e}") from e
