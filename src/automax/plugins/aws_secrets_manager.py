"""
Plugin for retrieving and writing secrets from/to AWS Secrets Manager.
"""

import base64
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    import boto3
    from botocore.exceptions import (
        ClientError,
        NoCredentialsError,
        PartialCredentialsError,
    )

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


@register_plugin
class AwsSecretsManagerPlugin(BasePlugin):
    """
    Retrieve and manage secrets from AWS Secrets Manager.
    """

    METADATA = PluginMetadata(
        name="aws_secrets_manager",
        version="2.0.0",
        description="Manage secrets in AWS Secrets Manager",
        author="Marco Fortina",
        category="cloud",
        tags=["aws", "secrets", "cloud"],
        required_config=["secret_name", "action"],
        optional_config=["value", "region_name", "profile_name", "role_arn"],
    )

    SCHEMA = {
        "secret_name": {"type": str, "required": True},
        "region_name": {"type": str, "required": False},
        "profile_name": {"type": str, "required": False},
        "role_arn": {"type": str, "required": False},
        "action": {"type": str, "required": True},  # read | write | create
        "value": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute an action on AWS Secrets Manager.

        Supported actions:
            - read   : get_secret_value()
            - write  : put_secret_value() or create if missing
            - create : create_secret()

        Returns:
            dict: secret_name, action, value (if available), status, aws_response

        Raises:
            PluginExecutionError: invalid action or AWS error

        """
        if not AWS_AVAILABLE:
            raise PluginExecutionError(
                "AWS SDK not installed. Install with: pip install boto3"
            )

        secret_name = self.config["secret_name"]
        region_name = self.config.get("region_name", "us-east-1")
        profile_name = self.config.get("profile_name")
        role_arn = self.config.get("role_arn")
        action = self.config.get("action").lower()

        self.logger.info(f"AWS Secrets Manager action={action} secret={secret_name}")

        valid_actions = {"read", "write", "create"}
        if action not in valid_actions:
            raise PluginExecutionError(
                f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            )

        try:
            client = self._get_client(region_name, profile_name, role_arn)

            if action == "read":
                try:
                    resp = client.get_secret_value(SecretId=secret_name)
                    value = resp.get("SecretString")
                    if value is None:
                        value = base64.b64encode(resp.get("SecretBinary", b"")).decode(
                            "utf-8"
                        )
                    result = {
                        "secret_name": secret_name,
                        "action": action,
                        "value": value,
                        "status": "success",
                    }

                    self.logger.info(f"Successfully retrieved secret: {secret_name}")
                    return result

                except ClientError as e:
                    code = e.response.get("Error", {}).get("Code")
                    if code in ("ResourceNotFoundException", "ResourceNotFound"):
                        raise PluginExecutionError(
                            f"Secret '{secret_name}' not found"
                        ) from e
                    raise

            elif action == "write":
                if "value" not in self.config:
                    raise PluginExecutionError("Missing 'value' for write action")
                try:
                    resp = client.put_secret_value(
                        SecretId=secret_name, SecretString=self.config["value"]
                    )
                    value = self.config.get("value")
                    result = {
                        "secret_name": secret_name,
                        "action": action,
                        "value": value,
                        "version_id": resp.get("VersionId"),
                        "status": "updated",
                    }

                    self.logger.info(
                        f"Successfully updated secret: {secret_name} (version {resp.get('VersionId')})"
                    )
                    return result

                except ClientError as e:
                    code = e.response.get("Error", {}).get("Code")
                    if code in ("ResourceNotFoundException", "ResourceNotFound"):
                        resp = client.create_secret(
                            Name=secret_name, SecretString=self.config.get("value", "")
                        )
                        value = self.config.get("value")
                        return {
                            "secret_name": secret_name,
                            "action": action,
                            "value": value,
                            "arn": resp.get("ARN"),
                            "status": "created",
                        }
                    raise

            elif action == "create":
                try:
                    resp = client.create_secret(
                        Name=secret_name, SecretString=self.config.get("value", "")
                    )
                    value = self.config.get("value")
                    result = {
                        "secret_name": secret_name,
                        "action": action,
                        "value": value,
                        "arn": resp.get("ARN"),
                        "status": "created",
                    }

                    self.logger.info(
                        f"Successfully created secret: {secret_name} (ARN: {resp.get('ARN')})"
                    )
                    return result

                except ClientError as e:
                    code = e.response.get("Error", {}).get("Code")
                    if code in (
                        "ResourceExistsException",
                        "ResourceAlreadyExistsException",
                    ):
                        raise PluginExecutionError(
                            f"Secret '{secret_name}' already exists"
                        ) from e
                    raise

            else:
                raise PluginExecutionError(f"Unsupported action: {action}")

        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            self.logger.error(f"AWS error: {e}")
            raise PluginExecutionError(str(e)) from e

    def _get_client(
        self, region_name: str, profile_name: str = None, role_arn: str = None
    ) -> boto3.client:
        """
        Create boto3 client with optional profile and assume-role support.
        """
        try:
            session_args = {}
            if profile_name:
                session_args["profile_name"] = profile_name
            session = boto3.Session(**session_args) if session_args else boto3.Session()

            if role_arn:
                sts = session.client("sts", region_name=region_name)
                creds = sts.assume_role(
                    RoleArn=role_arn, RoleSessionName="AutomaxSession"
                )["Credentials"]
                session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                )

            client = session.client("secretsmanager", region_name=region_name)
            self.logger.info(
                f"Successfully created AWS Secrets Manager client for region {region_name}"
            )
            return client

        except Exception as e:
            self.logger.error(f"Failed to create AWS client: {e}")
            raise PluginExecutionError(f"Failed to create AWS client: {e}") from e
