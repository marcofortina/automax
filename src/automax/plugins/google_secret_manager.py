"""
Plugin for Google Cloud Secret Manager integration.
"""

import json
import os
from typing import Any, Dict

from google.api_core import exceptions
from google.cloud import secretmanager
from google.oauth2 import service_account

from automax.core.exceptions import AutomaxError
from automax.core.utils.common_utils import echo


def get_secret_google_secret_manager(config: Dict[str, Any], logger=None):
    """
    Retrieve a secret from Google Cloud Secret Manager.

    Args:
        config: Configuration dictionary containing:
            - credentials_json: Service account JSON (optional)
            - project_id: GCP project ID (optional)
            - secret_id: The secret ID to retrieve
            - version: Secret version (default: "latest")
            - fail_fast: Whether to raise errors immediately (default: True)
        logger: Logger instance for logging

    Returns:
        str: The secret value

    Raises:
        AutomaxError: If secret retrieval fails and fail_fast is True
    """
    fail_fast = config.get("fail_fast", True)
    secret_id = config.get("secret_id")
    version = config.get("version", "latest")

    if not secret_id:
        msg = "secret_id is required for Google Secret Manager"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None

    try:
        # Initialize client with credentials
        credentials = _get_credentials(config)
        client = secretmanager.SecretManagerServiceClient(credentials=credentials)

        # Get project ID
        project_id = config.get("project_id")
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                msg = "Project ID must be provided in config or GOOGLE_CLOUD_PROJECT environment variable"
                if logger:
                    echo(msg, logger, level="ERROR")
                if fail_fast:
                    raise AutomaxError(msg, level="FATAL")
                return None

        # Build the resource name and access secret
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")

        if logger:
            echo(
                f"Retrieved secret '{secret_id}' from Google Cloud Secret Manager",
                logger,
                level="INFO",
            )

        return secret_value

    except exceptions.PermissionDenied as e:
        msg = f"Permission denied accessing secret '{secret_id}': {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None
    except exceptions.NotFound as e:
        msg = f"Secret '{secret_id}' not found: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None
    except Exception as e:
        msg = f"Failed to retrieve secret '{secret_id}' from Google Cloud Secret Manager: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None


def _get_credentials(config: Dict[str, Any]):
    """Get GCP credentials from config or environment."""
    credentials_json = config.get("credentials_json")

    if credentials_json:
        # Use provided service account JSON
        credentials_info = json.loads(credentials_json)
        return service_account.Credentials.from_service_account_info(credentials_info)

    # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS env var, metadata server, etc.)
    return None


REGISTER_UTILITIES = [
    ("get_secret_google_secret_manager", get_secret_google_secret_manager)
]

SCHEMA = {
    "credentials_json": {"type": str, "required": False},
    "project_id": {"type": str, "required": False},
    "secret_id": {"type": str, "required": True},
    "version": {"type": str, "default": "latest"},
    "fail_fast": {"type": bool, "default": True},
}
