"""
Tests for aws_secrets_manager plugin.
"""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError, NoCredentialsError
import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestAwsSecretsManagerPlugin:
    """
    Test suite for aws_secrets_manager plugin.
    """

    def test_aws_secrets_manager_plugin_registered(self):
        """
        Verify that aws_secrets_manager plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "aws_secrets_manager" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("aws_secrets_manager")
        assert metadata.name == "aws_secrets_manager"
        assert "aws" in metadata.tags
        assert "secret_name" in metadata.required_config

    def test_aws_secrets_manager_plugin_instantiation(self):
        """
        Verify aws_secrets_manager plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        config = {
            "secret_name": "my-test-secret",
            "region_name": "us-east-1",
            "profile_name": "default",
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_aws_secrets_manager_plugin_configuration_validation(self):
        """
        Verify aws_secrets_manager plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_execution_success(self, mock_session):
        """
        Test aws_secrets_manager plugin execution with successful secret retrieval.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

        mock_response = {
            "SecretString": "my_secret_value",
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret",
            "VersionId": "v1",
            "Name": "my-secret",
        }
        mock_secrets_client.get_secret_value.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class({"secret_name": "my-secret", "region_name": "us-east-1"})

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["secret_name"] == "my-secret"
        assert result["secret_value"] == "my_secret_value"
        assert result["secret_type"] == "string"
        assert result["region"] == "us-east-1"

        # Verify mock call
        mock_secrets_client.get_secret_value.assert_called_once_with(
            SecretId="my-secret"
        )

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_binary_secret(self, mock_session):
        """
        Test aws_secrets_manager plugin execution with binary secret.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

        import base64

        binary_data = b"binary_secret_data"
        mock_response = {
            "SecretBinary": binary_data,
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-binary-secret",
            "VersionId": "v1",
            "Name": "my-binary-secret",
        }
        mock_secrets_client.get_secret_value.return_value = mock_response

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class(
            {"secret_name": "my-binary-secret", "region_name": "us-east-1"}
        )

        result = plugin.execute()

        assert result["status"] == "success"
        assert result["secret_name"] == "my-binary-secret"
        assert result["secret_value"] == base64.b64encode(binary_data).decode("utf-8")
        assert result["secret_type"] == "binary"

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_secret_not_found(self, mock_session):
        """
        Test aws_secrets_manager plugin execution with secret not found.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Secret not found",
            }
        }
        mock_secrets_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class(
            {"secret_name": "nonexistent-secret", "region_name": "us-east-1"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Secret nonexistent-secret not found" in str(exc_info.value)

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_access_denied(self, mock_session):
        """
        Test aws_secrets_manager plugin execution with access denied.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

        error_response = {
            "Error": {"Code": "AccessDeniedException", "Message": "Access denied"}
        }
        mock_secrets_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class({"secret_name": "my-secret", "region_name": "us-east-1"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Access denied" in str(exc_info.value)

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_no_credentials(self, mock_session):
        """
        Test aws_secrets_manager plugin execution with no AWS credentials.
        """
        # Setup mock to raise exception
        mock_session.side_effect = NoCredentialsError()

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class({"secret_name": "my-secret", "region_name": "us-east-1"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Unable to locate credentials" in str(exc_info.value)

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_with_profile(self, mock_session):
        """
        Test aws_secrets_manager plugin execution with AWS profile.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

        mock_response = {
            "SecretString": "my_secret_value",
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret",
            "VersionId": "v1",
        }

        mock_secrets_client.get_secret_value.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class(
            {
                "secret_name": "my-secret",
                "region_name": "us-east-1",
                "profile_name": "my-profile",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"

        # Verify mock call
        mock_session.assert_called_once_with(profile_name="my-profile")
