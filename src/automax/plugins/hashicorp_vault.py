"""
Plugin for retrieving and writing secrets in HashiCorp Vault.
"""

from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    import hvac

    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False


@register_plugin
class HashiCorpVaultPlugin(BasePlugin):
    """
    Retrieve and manage secrets in HashiCorp Vault.
    """

    METADATA = PluginMetadata(
        name="hashicorp_vault",
        version="2.0.0",
        description="Manage secrets in HashiCorp Vault",
        author="Automax Team",
        category="cloud",
        tags=["vault", "hashicorp", "secrets"],
        required_config=["url", "mount_point", "path", "action"],
        optional_config=["token", "namespace", "value"],
    )

    SCHEMA = {
        "url": {"type": str, "required": True},
        "mount_point": {"type": str, "required": True},
        "path": {"type": str, "required": True},
        "token": {"type": str, "required": False},
        "namespace": {"type": str, "required": False},
        "action": {"type": str, "required": True},  # read | write | create
        "value": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute an operation on HashiCorp Vault Secrets.

        Supported actions:
            - read:   read_secret_version()
            - write:  create_or_update_secret()
            - create: same as write

        Returns:
            dict: containing path, mount_point, action,
                  value (if available), metadata, status.

        Raises:
            PluginExecutionError: for any SDK or Vault-related failure.

        """
        if not HVAC_AVAILABLE:
            raise PluginExecutionError(
                "hvac SDK not installed. Install with: pip install hvac"
            )

        mount = self.config["mount_point"]
        path = self.config["path"]
        action = self.config["action"].lower()

        self.logger.info(f"Vault action={action} mount={mount} path={path}")

        valid_actions = {"read", "write", "create"}
        if action not in valid_actions:
            raise PluginExecutionError(
                f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            )

        client = self._get_client()

        if action == "read":
            try:
                resp = client.secrets.kv.v2.read_secret_version(
                    path=path, mount_point=mount
                )

                data = resp.get("data", {}).get("data", {})
                metadata = resp.get("data", {}).get("metadata", {})

                result = {
                    "mount_point": mount,
                    "path": path,
                    "action": action,
                    "value": data,
                    "version": metadata.get("version"),
                    "created_time": metadata.get("created_time"),
                    "deletion_time": metadata.get("deletion_time"),
                    "destroyed": metadata.get("destroyed"),
                    "status": "success",
                }

                self.logger.info(f"Successfully read secret at {mount}/{path}")
                return result

            except Exception as e:
                self.logger.error(f"HashiCorp Vault read error: {e}")
                raise PluginExecutionError(str(e)) from e

        elif action in ("write", "create"):
            if "value" not in self.config:
                raise PluginExecutionError("Missing 'value' for write/create action")

            try:
                client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    mount_point=mount,
                    secret={"value": self.config["value"]},
                )

                result = {
                    "mount_point": mount,
                    "path": path,
                    "action": action,
                    "value": self.config["value"],
                    "status": "written",
                }

                self.logger.info(f"Successfully {action} secret at {mount}/{path}")
                return result

            except Exception as e:
                self.logger.error(f"HashiCorp Vault {action} error: {e}")
                raise PluginExecutionError(str(e)) from e

        else:
            raise PluginExecutionError(f"Unsupported action: {action}")

    def _get_client(self) -> hvac.Client:
        """
        Create and authenticate an hvac.Client using optional token and namespace.

        Raises:
            PluginExecutionError: on connection/authentication errors.

        """
        try:
            token = self.config.get("token")
            namespace = self.config.get("namespace")

            self.logger.info("Initializing HashiCorp Vault client")

            client = hvac.Client(
                url=self.config["url"],
                token=token,
                namespace=namespace,
            )

            if not client.is_authenticated():
                raise PluginExecutionError("Vault authentication failed")

            self.logger.info("Successfully created and authenticated Vault client")
            return client

        except Exception as e:
            self.logger.error(f"Failed to create Vault client: {e}")
            raise PluginExecutionError(f"Failed to create Vault client: {e}") from e
