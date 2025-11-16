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
        assert "action" in metadata.required_config

    def test_aws_secrets_manager_plugin_instantiation(self):
        """
        Verify aws_secrets_manager plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        config = {
            "secret_name": "my-test-secret",
            "action": "read",
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
    def test_aws_secrets_manager_plugin_read_success(self, mock_session):
        """
        Test aws_secrets_manager plugin read action with successful secret retrieval.
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
        plugin = plugin_class(
            {"secret_name": "my-secret", "action": "read", "region_name": "us-east-1"}
        )

        result = plugin.execute()

        # Verify result structure - allineata al nuovo plugin
        assert result["status"] == "success"
        assert result["secret_name"] == "my-secret"
        assert result["action"] == "read"
        assert result["value"] == "my_secret_value"

        # Verify mock call
        mock_secrets_client.get_secret_value.assert_called_once_with(
            SecretId="my-secret"
        )

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_read_binary_secret(self, mock_session):
        """
        Test aws_secrets_manager plugin read action with binary secret.
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
            {
                "secret_name": "my-binary-secret",
                "action": "read",
                "region_name": "us-east-1",
            }
        )

        result = plugin.execute()

        assert result["status"] == "success"
        assert result["secret_name"] == "my-binary-secret"
        assert result["action"] == "read"
        assert result["value"] == base64.b64encode(binary_data).decode("utf-8")

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_write_existing_secret(self, mock_session):
        """
        Test aws_secrets_manager plugin write action with existing secret.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

        mock_response = {
            "VersionId": "v2",
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret",
        }
        mock_secrets_client.put_secret_value.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class(
            {
                "secret_name": "my-secret",
                "action": "write",
                "value": "new_secret_value",
                "region_name": "us-east-1",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "updated"
        assert result["secret_name"] == "my-secret"
        assert result["action"] == "write"
        assert result["value"] == "new_secret_value"
        assert result["version_id"] == "v2"

        # Verify mock call
        mock_secrets_client.put_secret_value.assert_called_once_with(
            SecretId="my-secret", SecretString="new_secret_value"
        )

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_create_secret(self, mock_session):
        """
        Test aws_secrets_manager plugin create action.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

        mock_response = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:new-secret"
        }
        mock_secrets_client.create_secret.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("aws_secrets_manager")
        plugin = plugin_class(
            {
                "secret_name": "new-secret",
                "action": "create",
                "value": "secret_value",
                "region_name": "us-east-1",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "created"
        assert result["secret_name"] == "new-secret"
        assert result["action"] == "create"
        assert result["value"] == "secret_value"
        assert "arn" in result

        # Verify mock call
        mock_secrets_client.create_secret.assert_called_once_with(
            Name="new-secret", SecretString="secret_value"
        )

    @patch("automax.plugins.aws_secrets_manager.boto3.Session")
    def test_aws_secrets_manager_plugin_read_secret_not_found(self, mock_session):
        """
        Test aws_secrets_manager plugin read action with secret not found.
        """
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_secrets_client = MagicMock()
        mock_session_instance.client.return_value = mock_secrets_client

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
            {
                "secret_name": "nonexistent-secret",
                "action": "read",
                "region_name": "us-east-1",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Secret 'nonexistent-secret' not found" in str(exc_info.value)

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
        plugin = plugin_class(
            {"secret_name": "my-secret", "action": "read", "region_name": "us-east-1"}
        )

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
        plugin = plugin_class(
            {"secret_name": "my-secret", "action": "read", "region_name": "us-east-1"}
        )

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
                "action": "read",
                "region_name": "us-east-1",
                "profile_name": "my-profile",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"

        # Verify mock call
        mock_session.assert_called_once_with(profile_name="my-profile")
