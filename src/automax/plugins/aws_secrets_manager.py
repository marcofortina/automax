"""
Plugin for retrieving secrets from AWS Secrets Manager.
"""

from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class AwsSecretsManagerPlugin(BasePlugin):
    """
    Retrieve secrets from AWS Secrets Manager.
    """

    METADATA = PluginMetadata(
        name="aws_secrets_manager",
        version="2.0.0",
        description="Retrieve secrets from AWS Secrets Manager",
        author="Automax Team",
        category="cloud",
        tags=["aws", "secrets", "cloud"],
        required_config=["secret_name"],
        optional_config=["region_name", "profile_name", "role_arn"],
    )

    SCHEMA = {
        "secret_name": {"type": str, "required": True},
        "region_name": {"type": str, "required": False},
        "profile_name": {"type": str, "required": False},
        "role_arn": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Retrieve a secret from AWS Secrets Manager.

        Returns:
            Dictionary containing the secret value and metadata.

        Raises:
            PluginExecutionError: If the secret cannot be retrieved.

        """
        secret_name = self.config["secret_name"]
        region_name = self.config.get("region_name", "us-east-1")
        profile_name = self.config.get("profile_name")
        role_arn = self.config.get("role_arn")

        self.logger.info(f"Retrieving secret: {secret_name} from region: {region_name}")

        try:
            client = self._create_client(region_name, profile_name, role_arn)
            response = client.get_secret_value(SecretId=secret_name)

            # AWS Secrets Manager può restituire segreti come stringa o binari
            if "SecretString" in response:
                secret_value = response["SecretString"]
                secret_type = "string"
            else:
                # Per segreti binari, decodifichiamo in base64 o restituiamo come stringa
                import base64

                secret_value = base64.b64encode(response["SecretBinary"]).decode(
                    "utf-8"
                )
                secret_type = "binary"

            result = {
                "secret_name": secret_name,
                "secret_value": secret_value,
                "secret_type": secret_type,
                "secret_arn": response.get("ARN", ""),
                "version_id": response.get("VersionId", ""),
                "region": region_name,
                "status": "success",
            }

            self.logger.info(f"Successfully retrieved secret: {secret_name}")
            return result

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            self.logger.error(
                f"AWS Secrets Manager error [{error_code}]: {error_message}"
            )

            if error_code == "ResourceNotFoundException":
                raise PluginExecutionError(
                    f"Secret {secret_name} not found in AWS Secrets Manager"
                ) from e
            elif error_code == "AccessDeniedException":
                raise PluginExecutionError(
                    f"Access denied to secret {secret_name}. Check IAM permissions."
                ) from e
            elif error_code == "DecryptionFailure":
                raise PluginExecutionError(
                    f"Failed to decrypt secret {secret_name}. Check KMS permissions."
                ) from e
            elif error_code == "InternalServiceError":
                raise PluginExecutionError(
                    f"AWS Secrets Manager internal error for secret {secret_name}"
                ) from e
            else:
                raise PluginExecutionError(
                    f"AWS Secrets Manager error: {error_message}"
                ) from e

        except (NoCredentialsError, PartialCredentialsError) as e:
            error_msg = "AWS credentials not found or incomplete. Configure AWS CLI or environment variables."
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error retrieving secret {secret_name}: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

    def _create_client(
        self, region_name: str, profile_name: str = None, role_arn: str = None
    ) -> boto3.client:
        """
        Create a boto3 client for AWS Secrets Manager.
        """
        try:
            session_args = {}
            if profile_name:
                session_args["profile_name"] = profile_name

            session = boto3.Session(**session_args)

            # Se è specificato un role_arn, assumiamo il ruolo
            if role_arn:
                sts_client = session.client("sts", region_name=region_name)
                response = sts_client.assume_role(
                    RoleArn=role_arn, RoleSessionName="AutomaxSecretsManagerSession"
                )
                credentials = response["Credentials"]

                # Creiamo una nuova sessione con le credenziali assunte
                session = boto3.Session(
                    aws_access_key_id=credentials["AccessKeyId"],
                    aws_secret_access_key=credentials["SecretAccessKey"],
                    aws_session_token=credentials["SessionToken"],
                )

            return session.client("secretsmanager", region_name=region_name)

        except Exception as e:
            self.logger.error(f"Failed to create AWS client: {e}")
            raise PluginExecutionError(f"Failed to create AWS client: {e}") from e
