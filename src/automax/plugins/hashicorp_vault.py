"""
Plugin for Hashicorp Vault integration.
"""

from typing import Any, Dict

import hvac

from automax.core.exceptions import AutomaxError
from automax.core.utils.common_utils import echo


def vault_read_secret(
    vault_url: str,
    secret_path: str,
    auth_method: str = "token",
    auth_config: Dict[str, Any] = None,
    kv_version: int = 2,
    mount_point: str = "secret",
    logger=None,
    fail_fast: bool = True,
) -> Dict[str, Any]:
    """
    Read secret from Hashicorp Vault.

    Args:
        vault_url (str): Vault server URL.
        secret_path (str): Path to the secret.
        auth_method (str): Authentication method (token, approle).
        auth_config (dict): Authentication configuration.
        kv_version (int): KV secrets engine version (1 or 2).
        mount_point (str): Mount point for secrets engine.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        dict: Secret data.

    Raises:
        AutomaxError: If fail_fast is True and operation fails.

    """
    try:
        # Initialize Vault client
        client = hvac.Client(url=vault_url)

        # Authenticate
        if auth_method == "token":
            if not auth_config or "token" not in auth_config:
                raise AutomaxError(
                    "Token authentication requires 'token' in auth_config"
                )
            client.token = auth_config["token"]
        elif auth_method == "approle":
            if (
                not auth_config
                or "role_id" not in auth_config
                or "secret_id" not in auth_config
            ):
                raise AutomaxError(
                    "AppRole authentication requires 'role_id' and 'secret_id'"
                )
            auth_response = client.auth.approle.login(
                role_id=auth_config["role_id"], secret_id=auth_config["secret_id"]
            )
            client.token = auth_response["auth"]["client_token"]
        else:
            raise AutomaxError(f"Unsupported authentication method: {auth_method}")

        # Verify authentication
        if not client.is_authenticated():
            raise AutomaxError("Vault authentication failed")

        # Read secret
        if kv_version == 2:
            response = client.secrets.kv.v2.read_secret_version(
                path=secret_path, mount_point=mount_point
            )
            secret_data = response["data"]["data"]
        else:
            response = client.secrets.kv.v1.read_secret(
                path=secret_path, mount_point=mount_point
            )
            secret_data = response["data"]

        if logger:
            echo(
                f"Successfully read secret from Vault: {secret_path}",
                logger,
                level="INFO",
            )

        return secret_data

    except Exception as e:
        msg = f"Vault read secret failed: {str(e)}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return {}


def vault_write_secret(
    vault_url: str,
    secret_path: str,
    secret_data: Dict[str, Any],
    auth_method: str = "token",
    auth_config: Dict[str, Any] = None,
    kv_version: int = 2,
    mount_point: str = "secret",
    logger=None,
    fail_fast: bool = True,
) -> bool:
    """
    Write secret to Hashicorp Vault.

    Args:
        vault_url (str): Vault server URL.
        secret_path (str): Path to the secret.
        secret_data (dict): Secret data to write.
        auth_method (str): Authentication method (token, approle).
        auth_config (dict): Authentication configuration.
        kv_version (int): KV secrets engine version (1 or 2).
        mount_point (str): Mount point for secrets engine.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        bool: True if successful.

    Raises:
        AutomaxError: If fail_fast is True and operation fails.

    """
    try:
        # Initialize Vault client (same as read)
        client = hvac.Client(url=vault_url)

        # Authenticate (same as read)
        if auth_method == "token":
            if not auth_config or "token" not in auth_config:
                raise AutomaxError(
                    "Token authentication requires 'token' in auth_config"
                )
            client.token = auth_config["token"]
        elif auth_method == "approle":
            if (
                not auth_config
                or "role_id" not in auth_config
                or "secret_id" not in auth_config
            ):
                raise AutomaxError(
                    "AppRole authentication requires 'role_id' and 'secret_id'"
                )
            auth_response = client.auth.approle.login(
                role_id=auth_config["role_id"], secret_id=auth_config["secret_id"]
            )
            client.token = auth_response["auth"]["client_token"]
        else:
            raise AutomaxError(f"Unsupported authentication method: {auth_method}")

        if not client.is_authenticated():
            raise AutomaxError("Vault authentication failed")

        # Write secret
        if kv_version == 2:
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_path, secret=secret_data, mount_point=mount_point
            )
        else:
            client.secrets.kv.v1.create_or_update_secret(
                path=secret_path, secret=secret_data, mount_point=mount_point
            )

        if logger:
            echo(
                f"Successfully wrote secret to Vault: {secret_path}",
                logger,
                level="INFO",
            )

        return True

    except Exception as e:
        msg = f"Vault write secret failed: {str(e)}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return False


REGISTER_UTILITIES = [
    ("vault_read_secret", vault_read_secret),
    ("vault_write_secret", vault_write_secret),
]

SCHEMA = {
    "vault_read_secret": {
        "vault_url": {"type": str, "required": True},
        "secret_path": {"type": str, "required": True},
        "auth_method": {"type": str, "default": "token"},
        "auth_config": {"type": dict, "default": {}},
        "kv_version": {"type": int, "default": 2},
        "mount_point": {"type": str, "default": "secret"},
        "fail_fast": {"type": bool, "default": True},
    },
    "vault_write_secret": {
        "vault_url": {"type": str, "required": True},
        "secret_path": {"type": str, "required": True},
        "secret_data": {"type": dict, "required": True},
        "auth_method": {"type": str, "default": "token"},
        "auth_config": {"type": dict, "default": {}},
        "kv_version": {"type": int, "default": 2},
        "mount_point": {"type": str, "default": "secret"},
        "fail_fast": {"type": bool, "default": True},
    },
}
