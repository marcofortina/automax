"""
Tests for hashicorp_vault plugin.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestHashicorpVaultPlugin:
    """
    Test suite for hashicorp_vault plugin.
    """

    def test_hashicorp_vault_plugin_registered(self):
        """
        Verify that hashicorp_vault plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "hashicorp_vault" in global_registry.list_plugins()

        # Verify metadata matches the updated plugin
        metadata = global_registry.get_metadata("hashicorp_vault")
        assert metadata.name == "hashicorp_vault"
        assert metadata.version == "2.0.0"
        assert "vault" in metadata.tags
        assert "secrets" in metadata.description.lower()
        assert "url" in metadata.required_config
        assert "mount_point" in metadata.required_config
        assert "path" in metadata.required_config
        assert "action" in metadata.required_config

    def test_hashicorp_vault_plugin_instantiation(self):
        """
        Verify hashicorp_vault plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        config = {
            "url": "https://vault.example.com",
            "mount_point": "secret",
            "path": "my-app/credentials",
            "action": "read",
            "token": "s.1234567890",
            "namespace": "admin",
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_hashicorp_vault_plugin_configuration_validation(self):
        """
        Verify hashicorp_vault plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"url": "https://vault.example.com"})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_read_success(self, mock_client_class):
        """
        Test hashicorp_vault plugin read action with successful secret retrieval.
        """
        # Setup mock client and response
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True

        mock_response = {
            "data": {
                "data": {"username": "admin", "password": "secret123"},
                "metadata": {
                    "version": 1,
                    "created_time": "2023-01-01T00:00:00Z",
                    "deletion_time": "",
                    "destroyed": False,
                },
            }
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "secret",
                "path": "my-app/credentials",
                "action": "read",
                "token": "s.1234567890",
                "namespace": "admin",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["mount_point"] == "secret"
        assert result["path"] == "my-app/credentials"
        assert result["action"] == "read"
        assert result["value"] == {"username": "admin", "password": "secret123"}
        assert result["version"] == 1
        assert result["created_time"] == "2023-01-01T00:00:00Z"

        # Verify mock calls
        mock_client_class.assert_called_once_with(
            url="https://vault.example.com", token="s.1234567890", namespace="admin"
        )
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="my-app/credentials", mount_point="secret"
        )

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_write_success(self, mock_client_class):
        """
        Test hashicorp_vault plugin write action with successful secret creation.
        """
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "secret",
                "path": "my-app/credentials",
                "action": "write",
                "token": "s.1234567890",
                "value": "my-secret-value",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "written"
        assert result["mount_point"] == "secret"
        assert result["path"] == "my-app/credentials"
        assert result["action"] == "write"
        assert result["value"] == "my-secret-value"

        # Verify mock calls
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="my-app/credentials",
            mount_point="secret",
            secret={"value": "my-secret-value"},
        )

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_create_success(self, mock_client_class):
        """
        Test hashicorp_vault plugin create action (same as write).
        """
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "secret",
                "path": "my-app/credentials",
                "action": "create",
                "token": "s.1234567890",
                "value": "my-secret-value",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "written"
        assert result["action"] == "create"

        # Verify mock calls
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="my-app/credentials",
            mount_point="secret",
            secret={"value": "my-secret-value"},
        )

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_read_failure(self, mock_client_class):
        """
        Test hashicorp_vault plugin read action with Vault error.
        """
        # Setup mock client that raises exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Secret not found"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "secret",
                "path": "my-app/credentials",
                "action": "read",
                "token": "s.1234567890",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Secret not found" in str(exc_info.value)

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_write_missing_value(self, mock_client_class):
        """
        Test hashicorp_vault plugin write action with missing value.
        """
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "secret",
                "path": "my-app/credentials",
                "action": "write",
                "token": "s.1234567890",
                # missing value
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Missing 'value' for write/create action" in str(exc_info.value)

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_invalid_action(self, mock_client_class):
        """
        Test hashicorp_vault plugin with invalid action.
        """
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "secret",
                "path": "my-app/credentials",
                "action": "delete",  # invalid action
                "token": "s.1234567890",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Invalid action 'delete'" in str(exc_info.value)

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_authentication_failure(self, mock_client_class):
        """
        Test hashicorp_vault plugin with authentication failure.
        """
        # Setup mock client that fails authentication
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = False

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "secret",
                "path": "my-app/credentials",
                "action": "read",
                "token": "s.1234567890",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Vault authentication failed" in str(exc_info.value)

    def test_hashicorp_vault_plugin_hvac_not_installed(self):
        """
        Test hashicorp_vault plugin when hvac is not installed.
        """
        # Temporarily simulate hvac not being available
        import automax.plugins.hashicorp_vault as vault_module

        original_available = vault_module.HVAC_AVAILABLE
        vault_module.HVAC_AVAILABLE = False

        try:
            global_registry.load_all_plugins()

            plugin_class = global_registry.get_plugin_class("hashicorp_vault")
            plugin = plugin_class(
                {
                    "url": "https://vault.example.com",
                    "mount_point": "secret",
                    "path": "my-app/credentials",
                    "action": "read",
                    "token": "s.1234567890",
                }
            )

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "hvac SDK not installed" in str(exc_info.value)
        finally:
            # Restore original value
            vault_module.HVAC_AVAILABLE = original_available

    @patch("hvac.Client")
    def test_hashicorp_vault_plugin_without_namespace(self, mock_client_class):
        """
        Test hashicorp_vault plugin without namespace (optional parameter).
        """
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True

        mock_response = {
            "data": {"data": {"api_key": "abc123"}, "metadata": {"version": 1}}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "url": "https://vault.example.com",
                "mount_point": "kv",
                "path": "my-app",
                "action": "read",
                "token": "s.1234567890",
                # no namespace provided
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["mount_point"] == "kv"
        assert result["value"] == {"api_key": "abc123"}

        # Verify mock calls - namespace should be None
        mock_client_class.assert_called_once_with(
            url="https://vault.example.com", token="s.1234567890", namespace=None
        )
