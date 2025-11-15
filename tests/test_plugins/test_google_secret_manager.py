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
        assert "secret_id" in metadata.required_config

    def test_google_secret_manager_plugin_instantiation(self):
        """
        Verify google_secret_manager plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        config = {"project_id": "my-project", "secret_id": "my-secret"}

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
    def test_google_secret_manager_plugin_execution_success(self, mock_client):
        """
        Test google_secret_manager plugin execution with successful secret retrieval.
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
            {
                "project_id": "my-project",
                "secret_id": "my-secret",
                "version_id": "latest",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["project_id"] == "my-project"
        assert result["secret_id"] == "my-secret"
        assert result["secret_value"] == "my_google_secret"

        # Verify mock call
        mock_secret_client.access_secret_version.assert_called_once_with(
            request={"name": "projects/my-project/secrets/my-secret/versions/latest"}
        )
        mock_secret_client.access_secret_version.assert_called_once()

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_specific_version(self, mock_client):
        """
        Test google_secret_manager plugin execution with specific version.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        mock_response = MagicMock()
        mock_response.payload.data = b"my_google_secret_v2"
        mock_secret_client.access_secret_version.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {"project_id": "my-project", "secret_id": "my-secret", "version_id": "2"}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["version_id"] == "2"

        # Verify mock call
        mock_secret_client.access_secret_version.assert_called_once_with(
            request={"name": "projects/my-project/secrets/my-secret/versions/2"}
        )

    @patch(
        "automax.plugins.google_secret_manager.secretmanager.SecretManagerServiceClient"
    )
    def test_google_secret_manager_plugin_secret_not_found(self, mock_client):
        """
        Test google_secret_manager plugin execution with secret not found.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client

        # Setup mock to raise exception
        mock_secret_client.access_secret_version.side_effect = Exception(
            "Secret not found"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("google_secret_manager")
        plugin = plugin_class(
            {
                "project_id": "my-project",
                "secret_id": "nonexistent-secret",
                "version_id": "latest",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Failed to retrieve secret nonexistent-secret" in str(exc_info.value)

    def test_google_secret_manager_plugin_missing_sdk(self):
        """
        Test google_secret_manager plugin when SDK is not installed.
        """
        # Simulate missing Google Cloud SDK by blocking google.cloud imports
        with patch.dict(
            "sys.modules",
            {
                "google": None,
                "google.cloud": None,
                "google.cloud.secretmanager": None,
            },
        ):
            import importlib

            import automax.plugins.google_secret_manager

            # reset registry
            global_registry._plugins.pop("google_secret_manager", None)

            importlib.reload(automax.plugins.google_secret_manager)

            global_registry.load_all_plugins()

            plugin_class = global_registry.get_plugin_class("google_secret_manager")
            plugin = plugin_class(
                {"project_id": "my-project", "secret_id": "my-secret"}
            )

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Google Cloud SDK not installed" in str(exc_info.value)
