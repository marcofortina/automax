"""
Plugin for AWS Secrets Manager integration.
"""

import json

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from automax.core.exceptions import AutomaxError
from automax.core.utils.common_utils import echo


def aws_get_secret(
    secret_id: str,
    region_name: str = "us-east-1",
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None,
    version_stage: str = "AWSCURRENT",
    logger=None,
    fail_fast: bool = True,
):
    """
    Get secret value from AWS Secrets Manager.

    Args:
        secret_id (str): Secret identifier.
        region_name (str): AWS region name.
        aws_access_key_id (str): AWS access key ID.
        aws_secret_access_key (str): AWS secret access key.
        version_stage (str): Secret version stage.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        dict: Secret data.

    Raises:
        AutomaxError: If fail_fast is True and operation fails.
    """
    try:
        # Initialize AWS client
        client_config = {"region_name": region_name}

        if aws_access_key_id and aws_secret_access_key:
            client_config["aws_access_key_id"] = aws_access_key_id
            client_config["aws_secret_access_key"] = aws_secret_access_key

        client = boto3.client("secretsmanager", **client_config)

        # Get secret value
        response = client.get_secret_value(
            SecretId=secret_id, VersionStage=version_stage
        )

        # Parse secret string
        secret_string = response["SecretString"]
        try:
            secret_data = json.loads(secret_string)
        except json.JSONDecodeError:
            secret_data = secret_string

        if logger:
            echo(
                f"Successfully retrieved secret from AWS: {secret_id}",
                logger,
                level="INFO",
            )

        return secret_data

    except NoCredentialsError:
        msg = "AWS credentials not found"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return {}
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        msg = f"AWS Secrets Manager error ({error_code}): {error_message}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return {}
    except Exception as e:
        msg = f"AWS get secret failed: {str(e)}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return {}


def aws_create_secret(
    secret_id: str,
    secret_data: dict,
    region_name: str = "us-east-1",
    aws_access_key_id: str = None,
    aws_secret_access_key: str = None,
    description: str = "",
    logger=None,
    fail_fast: bool = True,
) -> bool:
    """
    Create secret in AWS Secrets Manager.

    Args:
        secret_id (str): Secret identifier.
        secret_data (dict): Secret data to store.
        region_name (str): AWS region name.
        aws_access_key_id (str): AWS access key ID.
        aws_secret_access_key (str): AWS secret access key.
        description (str): Secret description.
        logger (LoggerManager, optional): Logger instance.
        fail_fast (bool): If True, raise AutomaxError on failure.

    Returns:
        bool: True if successful.

    Raises:
        AutomaxError: If fail_fast is True and operation fails.
    """
    try:
        # Initialize AWS client
        client_config = {"region_name": region_name}

        if aws_access_key_id and aws_secret_access_key:
            client_config["aws_access_key_id"] = aws_access_key_id
            client_config["aws_secret_access_key"] = aws_secret_access_key

        client = boto3.client("secretsmanager", **client_config)

        # Convert secret data to JSON string
        if isinstance(secret_data, dict):
            secret_string = json.dumps(secret_data)
        else:
            secret_string = str(secret_data)

        # Create secret
        client.create_secret(
            Name=secret_id, SecretString=secret_string, Description=description
        )

        if logger:
            echo(
                f"Successfully created secret in AWS: {secret_id}", logger, level="INFO"
            )

        return True

    except NoCredentialsError:
        msg = "AWS credentials not found"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return False
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        msg = f"AWS Secrets Manager error ({error_code}): {error_message}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return False
    except Exception as e:
        msg = f"AWS create secret failed: {str(e)}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return False


REGISTER_UTILITIES = [
    ("aws_get_secret", aws_get_secret),
    ("aws_create_secret", aws_create_secret),
]

SCHEMA = {
    "aws_get_secret": {
        "secret_id": {"type": str, "required": True},
        "region_name": {"type": str, "default": "us-east-1"},
        "aws_access_key_id": {"type": str, "default": None},
        "aws_secret_access_key": {"type": str, "default": None},
        "version_stage": {"type": str, "default": "AWSCURRENT"},
        "fail_fast": {"type": bool, "default": True},
    },
    "aws_create_secret": {
        "secret_id": {"type": str, "required": True},
        "secret_data": {"type": dict, "required": True},
        "region_name": {"type": str, "default": "us-east-1"},
        "aws_access_key_id": {"type": str, "default": None},
        "aws_secret_access_key": {"type": str, "default": None},
        "description": {"type": str, "default": ""},
        "fail_fast": {"type": bool, "default": True},
    },
}
