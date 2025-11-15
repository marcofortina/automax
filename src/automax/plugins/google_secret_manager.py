"""
Plugin for retrieving secrets from Google Cloud Secret Manager.
"""

from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    from google.cloud import secretmanager

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


@register_plugin
class GoogleSecretManagerPlugin(BasePlugin):
    """
    Retrieve secrets from Google Cloud Secret Manager.
    """

    METADATA = PluginMetadata(
        name="google_secret_manager",
        version="2.0.0",
        description="Retrieve secrets from Google Cloud Secret Manager",
        author="Automax Team",
        category="cloud",
        tags=["google", "gcp", "secrets", "cloud"],
        required_config=["project_id", "secret_id"],
        optional_config=["version_id"],
    )

    SCHEMA = {
        "project_id": {"type": str, "required": True},
        "secret_id": {"type": str, "required": True},
        "version": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Retrieve a secret from Google Cloud Secret Manager.

        Returns:
            Dictionary containing the secret value and metadata.

        Raises:
            PluginExecutionError: If the secret cannot be retrieved.

        """
        if not GOOGLE_AVAILABLE:
            raise PluginExecutionError(
                "Google Cloud SDK not installed. Install with: pip install google-cloud-secret-manager"
            )

        project_id = self.config["project_id"]
        secret_id = self.config["secret_id"]
        version_id = self.config.get("version_id", "latest")

        self.logger.info(f"Retrieving secret: {secret_id} from project: {project_id}")

        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_name = (
                f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
            )
            response = client.access_secret_version(request={"name": secret_name})
            secret_value = response.payload.data.decode("UTF-8")

            result = {
                "project_id": project_id,
                "secret_id": secret_id,
                "version_id": version_id,
                "secret_value": secret_value,
                "status": "success",
            }

            self.logger.info(f"Successfully retrieved secret: {secret_id}")
            return result

        except Exception as e:
            error_msg = (
                f"Failed to retrieve secret {secret_id} from Google Secret Manager: {e}"
            )
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
