"""
Plugin for Azure Key Vault integration.
"""

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from automax.core.exceptions import AutomaxError
from automax.core.utils.common_utils import echo


def azure_get_secret(
    vault_url: str,
    secret_name: str,
    auth_method: str = "default",
    tenant_id: str = None,
    client_id: str = None,
    client_secret: str = None,
    logger=None,
    fail_fast: bool = True,
) -> str:
    """
    Get secret from Azure Key Vault.

    Args:
        vault_url (str): Azure Key Vault URL.
        secret_name (str): Name of the secret.
        auth_method (str): Authentication method (default, client_secret).
        tenant_id (str): Azure tenant ID (for client_secret auth).
        client_id (str): Azure client ID (for client_secret auth).
        client_secret (str): Azure client secret (for client_secret auth).
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        str: Secret value.

    Raises:
        AutomaxError: If fail_fast is True and operation fails.
    """
    try:
        # Initialize credential based on authentication method
        if auth_method == "default":
            credential = DefaultAzureCredential()
        elif auth_method == "client_secret":
            if not all([tenant_id, client_id, client_secret]):
                raise AutomaxError(
                    "client_secret authentication requires tenant_id, client_id, and client_secret"
                )
            credential = ClientSecretCredential(
                tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
            )
        else:
            raise AutomaxError(f"Unsupported authentication method: {auth_method}")

        # Initialize secret client
        secret_client = SecretClient(vault_url=vault_url, credential=credential)

        # Get secret
        secret = secret_client.get_secret(secret_name)

        if logger:
            echo(
                f"Successfully retrieved secret from Azure: {secret_name}",
                logger,
                level="INFO",
            )

        return secret.value

    except ResourceNotFoundError:
        msg = f"Secret not found in Azure Key Vault: {secret_name}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return ""
    except Exception as e:
        msg = f"Azure get secret failed: {str(e)}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return ""


def azure_set_secret(
    vault_url: str,
    secret_name: str,
    secret_value: str,
    auth_method: str = "default",
    tenant_id: str = None,
    client_id: str = None,
    client_secret: str = None,
    logger=None,
    fail_fast: bool = True,
) -> bool:
    """
    Set secret in Azure Key Vault.

    Args:
        vault_url (str): Azure Key Vault URL.
        secret_name (str): Name of the secret.
        secret_value (str): Secret value to store.
        auth_method (str): Authentication method (default, client_secret).
        tenant_id (str): Azure tenant ID (for client_secret auth).
        client_id (str): Azure client ID (for client_secret auth).
        client_secret (str): Azure client secret (for client_secret auth).
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        bool: True if successful.

    Raises:
        AutomaxError: If fail_fast is True and operation fails.
    """
    try:
        # Initialize credential based on authentication method
        if auth_method == "default":
            credential = DefaultAzureCredential()
        elif auth_method == "client_secret":
            if not all([tenant_id, client_id, client_secret]):
                raise AutomaxError(
                    "client_secret authentication requires tenant_id, client_id, and client_secret"
                )
            credential = ClientSecretCredential(
                tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
            )
        else:
            raise AutomaxError(f"Unsupported authentication method: {auth_method}")

        # Initialize secret client
        secret_client = SecretClient(vault_url=vault_url, credential=credential)

        # Set secret
        secret_client.set_secret(secret_name, secret_value)

        if logger:
            echo(
                f"Successfully set secret in Azure: {secret_name}", logger, level="INFO"
            )

        return True

    except Exception as e:
        msg = f"Azure set secret failed: {str(e)}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return False


REGISTER_UTILITIES = [
    ("azure_get_secret", azure_get_secret),
    ("azure_set_secret", azure_set_secret),
]

SCHEMA = {
    "azure_get_secret": {
        "vault_url": {"type": str, "required": True},
        "secret_name": {"type": str, "required": True},
        "auth_method": {"type": str, "default": "default"},
        "tenant_id": {"type": str, "default": None},
        "client_id": {"type": str, "default": None},
        "client_secret": {"type": str, "default": None},
        "fail_fast": {"type": bool, "default": True},
    },
    "azure_set_secret": {
        "vault_url": {"type": str, "required": True},
        "secret_name": {"type": str, "required": True},
        "secret_value": {"type": str, "required": True},
        "auth_method": {"type": str, "default": "default"},
        "tenant_id": {"type": str, "default": None},
        "client_id": {"type": str, "default": None},
        "client_secret": {"type": str, "default": None},
        "fail_fast": {"type": bool, "default": True},
    },
}
