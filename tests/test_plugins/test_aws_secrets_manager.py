"""
Unit tests for AWS Secrets Manager plugin.
"""

import json
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError, NoCredentialsError

from automax.plugins.aws_secrets_manager import aws_create_secret, aws_get_secret


class TestAWSSecretsManagerPlugin:
    """
    Test suite for AWS Secrets Manager plugin.
    """

    def setup_method(self):
        """
        Set up test fixtures.
        """
        self.mock_logger = Mock()

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_get_secret_success_json(self, mock_boto_client):
        """
        Test successful secret retrieval with JSON data.
        """
        # Mock setup
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            "Name": "test-secret",
            "SecretString": '{"username": "test-user", "password": "test-pass"}',
            "VersionStages": ["AWSCURRENT"],
        }
        mock_boto_client.return_value = mock_client

        # Execute
        result = aws_get_secret(
            secret_id="test-secret", region_name="us-east-1", logger=self.mock_logger
        )

        # Assertions
        mock_boto_client.assert_called_once_with(
            "secretsmanager", region_name="us-east-1"
        )
        mock_client.get_secret_value.assert_called_once_with(
            SecretId="test-secret", VersionStage="AWSCURRENT"
        )
        assert result == {"username": "test-user", "password": "test-pass"}

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_get_secret_success_string(self, mock_boto_client):
        """
        Test successful secret retrieval with string data.
        """
        # Mock setup
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            "Name": "test-secret",
            "SecretString": "plain-text-secret",
            "VersionStages": ["AWSCURRENT"],
        }
        mock_boto_client.return_value = mock_client

        # Execute
        result = aws_get_secret(secret_id="test-secret")

        # Should return string as-is
        assert result == "plain-text-secret"

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_get_secret_with_credentials(self, mock_boto_client):
        """
        Test secret retrieval with explicit credentials.
        """
        # Mock setup
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            "Name": "test-secret",
            "SecretString": '{"api_key": "test-key"}',
            "VersionStages": ["AWSCURRENT"],
        }
        mock_boto_client.return_value = mock_client

        # Execute with credentials
        result = aws_get_secret(
            secret_id="test-secret",
            region_name="us-east-1",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )

        # Assertions
        mock_boto_client.assert_called_once_with(
            "secretsmanager",
            region_name="us-east-1",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )
        assert result == {"api_key": "test-key"}

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_get_secret_no_credentials_error(self, mock_boto_client):
        """
        Test NoCredentialsError handling.
        """
        # Mock setup
        mock_boto_client.side_effect = NoCredentialsError()

        # Execute with fail_fast=False
        result = aws_get_secret(
            secret_id="test-secret", region_name="us-east-1", fail_fast=False
        )

        # Should return empty dict instead of raising exception
        assert result == {}

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_get_secret_client_error(self, mock_boto_client):
        """
        Test ClientError handling.
        """
        # Mock setup
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Secret not found",
                }
            },
            "GetSecretValue",
        )
        mock_boto_client.return_value = mock_client

        # Execute with fail_fast=False
        result = aws_get_secret(
            secret_id="non-existent-secret", region_name="us-east-1", fail_fast=False
        )

        # Should return empty dict instead of raising exception
        assert result == {}

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_create_secret_success(self, mock_boto_client):
        """
        Test successful secret creation.
        """
        # Mock setup
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        # Execute
        result = aws_create_secret(
            secret_id="new-secret",
            secret_data={"api_key": "test-key", "api_secret": "test-secret"},
            region_name="us-east-1",
            description="Test API credentials",
            logger=self.mock_logger,
        )

        # Assertions
        mock_client.create_secret.assert_called_once_with(
            Name="new-secret",
            SecretString=json.dumps(
                {"api_key": "test-key", "api_secret": "test-secret"}
            ),
            Description="Test API credentials",
        )
        assert result is True

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_create_secret_string_data(self, mock_boto_client):
        """
        Test secret creation with string data.
        """
        # Mock setup
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        # Execute with string data
        result = aws_create_secret(
            secret_id="new-secret",
            secret_data="plain-text-secret",
            region_name="us-east-1",
        )

        # Assertions
        mock_client.create_secret.assert_called_once_with(
            Name="new-secret", SecretString="plain-text-secret", Description=""
        )
        assert result is True

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_create_secret_no_credentials_error(self, mock_boto_client):
        """
        Test NoCredentialsError handling in create secret.
        """
        # Mock setup
        mock_boto_client.side_effect = NoCredentialsError()

        # Execute with fail_fast=False
        result = aws_create_secret(
            secret_id="new-secret",
            secret_data={"key": "value"},
            region_name="us-east-1",
            fail_fast=False,
        )

        # Should return False instead of raising exception
        assert result is False

    @patch("automax.plugins.aws_secrets_manager.boto3.client")
    def test_aws_create_secret_client_error(self, mock_boto_client):
        """
        Test ClientError handling in create secret.
        """
        # Mock setup
        mock_client = Mock()
        mock_client.create_secret.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceExistsException",
                    "Message": "Secret already exists",
                }
            },
            "CreateSecret",
        )
        mock_boto_client.return_value = mock_client

        # Execute with fail_fast=False
        result = aws_create_secret(
            secret_id="existing-secret",
            secret_data={"key": "value"},
            region_name="us-east-1",
            fail_fast=False,
        )

        # Should return False instead of raising exception
        assert result is False
