"""
Plugin for retrieving and writing secrets in Google Secret Manager.
"""

from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    from google.api_core.exceptions import GoogleAPIError
    from google.cloud import secretmanager

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


@register_plugin
class GoogleSecretManagerPlugin(BasePlugin):
    """
    Retrieve and manage secrets in Google Secret Manager.
    """

    METADATA = PluginMetadata(
        name="google_secret_manager",
        version="2.0.0",
        description="Manage secrets in Google Secret Manager",
        author="Marco Fortina",
        category="cloud",
        tags=["google", "gcp", "secrets"],
        required_config=["project_id", "secret_name", "action"],
        optional_config=["key_file_path", "value"],
    )

    SCHEMA = {
        "project_id": {"type": str, "required": True},
        "secret_name": {"type": str, "required": True},
        "key_file_path": {"type": str, "required": False},
        "action": {"type": str, "required": True},  # read | create | write/add_version
        "value": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute an action on Google Secret Manager.

        Supported actions:
            - read : access_secret_version()
            - create : create_secret()
            - write/add_version : add_secret_version()

        Returns:
            Dictionary containing:
                - project_id (str): The GCP project ID
                - secret_name (str): The name of the secret
                - action (str): The action performed (read, create, write/add_version)
                - value (str): The secret value (for read and write actions)
                - version_id (str): The version identifier (for read actions)
                - version_name (str): The full version name (for write actions)
                - status (str): Operation status (success, created, version_added)

        Raises:
            PluginExecutionError: If GCP credentials are invalid, secret not found,
                                insufficient permissions, or other GCP errors occur.

        """
        if not GOOGLE_AVAILABLE:
            raise PluginExecutionError("Google Secret Manager SDK not installed")

        project_id = self.config["project_id"]
        secret_name = self.config["secret_name"]
        action = self.config.get("action").lower()

        self.logger.info(f"Google Secret Manager action={action} secret={secret_name}")

        valid_actions = {"read", "write", "create", "add_version"}
        if action not in valid_actions:
            raise PluginExecutionError(
                f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            )

        client = self._get_client()
        resource = f"projects/{project_id}/secrets/{secret_name}"

        # Read secret
        if action == "read":
            try:
                resp = client.access_secret_version(
                    request={"name": f"{resource}/versions/latest"}
                )
                value = resp.payload.data.decode("utf-8")
                result = {
                    "project_id": project_id,
                    "secret_name": secret_name,
                    "version_id": "latest",
                    "value": value,
                    "status": "success",
                }

                self.logger.info(f"Successfully read secret: {secret_name}")
                return result

            except GoogleAPIError as e:
                self.logger.error(f"Google Secret Manager read error: {e}")
                raise PluginExecutionError(str(e)) from e

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise PluginExecutionError(str(e)) from e

        elif action == "create":
            try:
                resp = client.create_secret(
                    request={
                        "parent": f"projects/{project_id}",
                        "secret_id": secret_name,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
                result = {
                    "project_id": project_id,
                    "secret_name": secret_name,
                    "status": "created",
                }

                self.logger.info(f"Successfully created secret: {secret_name}")
                return result

            except GoogleAPIError as e:
                self.logger.error(f"Google Secret Manager create error: {e}")
                raise PluginExecutionError(str(e)) from e

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise PluginExecutionError(str(e)) from e

        elif action in ("write", "add_version"):
            if "value" not in self.config:
                raise PluginExecutionError(
                    "Missing 'value' for write/add_version action"
                )
            try:
                resp = client.add_secret_version(
                    request={
                        "parent": resource,
                        "payload": {"data": self.config["value"].encode("utf-8")},
                    }
                )
                result = {
                    "project_id": project_id,
                    "secret_name": secret_name,
                    "version_name": resp.name,
                    "value": self.config["value"],
                    "status": "version_added",
                }

                self.logger.info(f"Successfully added version to secret: {secret_name}")
                return result

            except GoogleAPIError as e:
                self.logger.error(f"Google Secret Manager add_version error: {e}")
                raise PluginExecutionError(str(e)) from e

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise PluginExecutionError(str(e)) from e

    def _get_client(self) -> secretmanager.SecretManagerServiceClient:
        """
        Create a Google Secret Manager client.
        """
        try:
            if "key_file_path" in self.config:
                client = (
                    secretmanager.SecretManagerServiceClient.from_service_account_file(
                        self.config["key_file_path"]
                    )
                )
            else:
                client = secretmanager.SecretManagerServiceClient()

            self.logger.info("Successfully created Google Secret Manager client")
            return client

        except Exception as e:
            self.logger.error(f"Failed to create Google Secret Manager client: {e}")
            raise PluginExecutionError(
                f"Failed to create Google Secret Manager client: {e}"
            ) from e
