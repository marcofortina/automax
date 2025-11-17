"""
Tests for google_secret_manager plugin.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestGoogleSecretManagerPlugin:
    """
    Test suite for google_secret_manager plugin.
    """

    def test_google_secret_manager_plugin_registered(self):
        """
        Verify that google_secret_manager plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "google_secret_manager" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("google_secret_manager")
        assert metadata.name == "google_secret_manager"
        assert "google" in metadata.tags
        assert "project_id" in metadata.required_config
        assert "secret_name" in metadata.required_config
        assert "action" in metadata.required_config

    def test_google_secret_manager_plugin_instantiation(self):
        """
        Verify google_secret_manager plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        config = {
            "project_id": "my-project",
            "secret_name": "my-secret",
            "action": "read",
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_google_secret_manager_plugin_configuration_validation(self):
        """
        Verify google_secret_manager plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"project_id": "my-project"})
        assert "required configuration" in str(exc_info.value).lower()

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_read_success(self, mock_client):
        """
        Test google_secret_manager plugin read action with successful secret retrieval.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        mock_response = MagicMock()
        mock_response.payload.data = b"my_google_secret"
        mock_secret_client.access_secret_version.return_value = mock_response

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {"project_id": "my-project", "secret_name": "my-secret", "action": "read"}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["project_id"] == "my-project"
        assert result["secret_name"] == "my-secret"
        assert result["value"] == "my_google_secret"
        assert result["version_id"] == "latest"

        # Verify mock call
        mock_secret_client.access_secret_version.assert_called_once_with(
            request={"name": "projects/my-project/secrets/my-secret/versions/latest"}
        )

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_create_success(self, mock_client):
        """
        Test google_secret_manager plugin create action.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        mock_response = MagicMock()
        mock_secret_client.create_secret.return_value = mock_response

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "new-secret",
                "action": "create",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "created"
        assert result["project_id"] == "my-project"
        assert result["secret_name"] == "new-secret"

        # Verify mock call
        mock_secret_client.create_secret.assert_called_once_with(
            request={
                "parent": "projects/my-project",
                "secret_id": "new-secret",
                "secret": {"replication": {"automatic": {}}},
            }
        )

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_write_success(self, mock_client):
        """
        Test google_secret_manager plugin write action.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        mock_response = MagicMock()
        mock_response.name = "projects/my-project/secrets/my-secret/versions/1"
        mock_secret_client.add_secret_version.return_value = mock_response

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "my-secret",
                "action": "write",
                "value": "new_secret_value",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "version_added"
        assert result["project_id"] == "my-project"
        assert result["secret_name"] == "my-secret"
        assert result["value"] == "new_secret_value"
        assert (
            result["version_name"] == "projects/my-project/secrets/my-secret/versions/1"
        )

        # Verify mock call
        mock_secret_client.add_secret_version.assert_called_once_with(
            request={
                "parent": "projects/my-project/secrets/my-secret",
                "payload": {"data": b"new_secret_value"},
            }
        )

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_add_version_success(self, mock_client):
        """
        Test google_secret_manager plugin add_version action.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        mock_response = MagicMock()
        mock_response.name = "projects/my-project/secrets/my-secret/versions/2"
        mock_secret_client.add_secret_version.return_value = mock_response

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "my-secret",
                "action": "add_version",
                "value": "another_secret_value",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "version_added"
        assert result["project_id"] == "my-project"
        assert result["secret_name"] == "my-secret"
        assert result["value"] == "another_secret_value"

        # Verify mock call
        mock_secret_client.add_secret_version.assert_called_once_with(
            request={
                "parent": "projects/my-project/secrets/my-secret",
                "payload": {"data": b"another_secret_value"},
            }
        )

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_read_secret_not_found(self, mock_client):
        """
        Test google_secret_manager plugin read action with secret not found.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        from google.api_core.exceptions import GoogleAPIError

        # Setup mock to raise exception
        mock_secret_client.access_secret_version.side_effect = GoogleAPIError(
            "Secret not found"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "nonexistent-secret",
                "action": "read",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Secret not found" in str(exc_info.value)

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_write_missing_value(self, mock_client):
        """
        Test google_secret_manager plugin write action with missing value.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "my-secret",
                "action": "write",
                # Missing 'value' parameter
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Missing 'value' for write/add_version action" in str(exc_info.value)

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_add_version_missing_value(self, mock_client):
        """
        Test google_secret_manager plugin add_version action with missing value.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "my-secret",
                "action": "add_version",
                # Missing 'value' parameter
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Missing 'value' for write/add_version action" in str(exc_info.value)

    def test_google_secret_manager_plugin_invalid_action(self):
        """
        Test google_secret_manager plugin with invalid action.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "my-secret",
                "action": "invalid_action",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Invalid action" in str(exc_info.value)

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_with_key_file(self, mock_client):
        """
        Test google_secret_manager plugin with service account key file.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.from_service_account_file.return_value = mock_secret_client

        mock_response = MagicMock()
        mock_response.payload.data = b"my_google_secret"
        mock_secret_client.access_secret_version.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_name": "my-secret",
                "action": "read",
                "key_file_path": "/path/to/key.json",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"

        # Verify mock call with key file
        mock_client.from_service_account_file.assert_called_once_with(
            "/path/to/key.json"
        )

    @patch("automax.plugins.google_secret_manager.GOOGLE_AVAILABLE", False)
    def test_google_secret_manager_plugin_missing_sdk(self):
        """
        Test google_secret_manager plugin when SDK is not installed.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {"project_id": "my-project", "secret_name": "my-secret", "action": "read"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Google Secret Manager SDK not installed" in str(exc_info.value)
