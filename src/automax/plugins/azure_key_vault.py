"""
Plugin for retrieving and writing secrets in Azure Key Vault.
"""

from typing import Any, Dict, Union

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    from azure.identity import ClientSecretCredential, DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


@register_plugin
class AzureKeyVaultPlugin(BasePlugin):
    """
    Retrieve and manage secrets in Azure Key Vault.
    """

    METADATA = PluginMetadata(
        name="azure_key_vault",
        version="2.0.0",
        description="Manage secrets in Azure Key Vault",
        author="Marco Fortina",
        category="cloud",
        tags=["azure", "secrets", "cloud"],
        required_config=["vault_url", "secret_name", "action"],
        optional_config=["tenant_id", "client_id", "client_secret", "value"],
    )

    SCHEMA = {
        "vault_url": {"type": str, "required": True},
        "secret_name": {"type": str, "required": True},
        "tenant_id": {"type": str, "required": False},
        "client_id": {"type": str, "required": False},
        "client_secret": {"type": str, "required": False},
        "action": {"type": str, "required": True},  # read | write | create
        "value": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute an operation on Azure Key Vault Secrets.

        Supported actions (via self.config['action']):
            - read  : get_secret()
            - write : set_secret()
            - create: same as write

        Returns:
            dict: secret_name, action, secret_value (if read/write), status

        Raises:
            PluginExecutionError: if action unsupported or Azure error

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
        action = self.config.get("action").lower()

        self.logger.info(
            f"Azure Key Vault action={action} secret={secret_name} vault_url={vault_url}"
        )

        valid_actions = {"read", "write", "create"}
        if action not in valid_actions:
            raise PluginExecutionError(
                f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            )

        credential = self._get_credential(tenant_id, client_id, client_secret)
        client = SecretClient(vault_url=vault_url, credential=credential)

        if action == "read":
            try:
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
                self.logger.error(f"Azure Key Vault read error: {e}")
                raise PluginExecutionError(str(e)) from e

        elif action in ("write", "create"):
            if "value" not in self.config:
                raise PluginExecutionError("Missing 'value' for write/create action")
            try:
                secret = client.set_secret(secret_name, self.config["value"])
                result = {
                    "vault_url": vault_url,
                    "secret_name": secret_name,
                    "secret_value": secret.value,
                    "action": action,
                    "status": "written",
                }

                self.logger.info(f"Successfully {action} secret: {secret_name}")
                return result

            except Exception as e:
                self.logger.error(f"Azure Key Vault write/create error: {e}")
                raise PluginExecutionError(str(e)) from e

    def _get_credential(
        self, tenant_id: str = None, client_id: str = None, client_secret: str = None
    ) -> Union[ClientSecretCredential, DefaultAzureCredential]:
        """
        Get Azure credential using various authentication methods.
        """
        try:
            if tenant_id and client_id and client_secret:
                credential = ClientSecretCredential(tenant_id, client_id, client_secret)
            else:
                credential = DefaultAzureCredential()

            self.logger.info("Successfully obtained Azure credential")
            return credential

        except Exception as e:
            self.logger.error(f"Failed to get Azure credential: {e}")
            raise PluginExecutionError(f"Failed to get Azure credential: {e}") from e
