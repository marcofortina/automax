"""
Tests for azure_key_vault plugin.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestAzureKeyVaultPlugin:
    """
    Test suite for azure_key_vault plugin.
    """

    def test_azure_key_vault_plugin_registered(self):
        """
        Verify that azure_key_vault plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "azure_key_vault" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("azure_key_vault")
        assert metadata.name == "azure_key_vault"
        assert "azure" in metadata.tags
        assert "vault_url" in metadata.required_config
        assert "secret_name" in metadata.required_config
        assert "action" in metadata.required_config

    def test_azure_key_vault_plugin_instantiation(self):
        """
        Verify azure_key_vault plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        config = {
            "vault_url": "https://my-vault.vault.azure.net/",
            "secret_name": "my-secret",
            "action": "read",
            "tenant_id": "tenant-123",
            "client_id": "client-456",
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_azure_key_vault_plugin_configuration_validation(self):
        """
        Verify azure_key_vault plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"vault_url": "https://vault.azure.net/"})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_key_vault_plugin_read_success(self, mock_credential, mock_client):
        """
        Test azure_key_vault plugin read action with successful secret retrieval.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client
        mock_credential.return_value = MagicMock()

        mock_secret = MagicMock()
        mock_secret.value = "my_azure_secret"
        mock_secret.properties.version = "v1"
        mock_secret.properties.enabled = True
        mock_secret.properties.expires_on = None
        mock_secret_client.get_secret.return_value = mock_secret

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "my-secret",
                "action": "read",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["vault_url"] == "https://my-vault.vault.azure.net/"
        assert result["secret_name"] == "my-secret"
        assert result["secret_value"] == "my_azure_secret"
        assert result["version"] == "v1"
        assert result["enabled"] is True
        assert result["expires_on"] is None

        # Verify mock calls
        mock_client.assert_called_once_with(
            vault_url="https://my-vault.vault.azure.net/",
            credential=mock_credential.return_value,
        )
        mock_secret_client.get_secret.assert_called_once_with("my-secret")

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_key_vault_plugin_write_success(self, mock_credential, mock_client):
        """
        Test azure_key_vault plugin write action with successful secret creation.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client
        mock_credential.return_value = MagicMock()

        mock_secret = MagicMock()
        mock_secret.value = "new_secret_value"
        mock_secret_client.set_secret.return_value = mock_secret

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "new-secret",
                "action": "write",
                "value": "new_secret_value",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "written"
        assert result["vault_url"] == "https://my-vault.vault.azure.net/"
        assert result["secret_name"] == "new-secret"
        assert result["secret_value"] == "new_secret_value"
        assert result["action"] == "write"

        # Verify mock calls
        mock_client.assert_called_once_with(
            vault_url="https://my-vault.vault.azure.net/",
            credential=mock_credential.return_value,
        )
        mock_secret_client.set_secret.assert_called_once_with(
            "new-secret", "new_secret_value"
        )

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_key_vault_plugin_create_success(self, mock_credential, mock_client):
        """
        Test azure_key_vault plugin create action with successful secret creation.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client
        mock_credential.return_value = MagicMock()

        mock_secret = MagicMock()
        mock_secret.value = "new_secret_value"
        mock_secret_client.set_secret.return_value = mock_secret

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "new-secret",
                "action": "create",
                "value": "new_secret_value",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "written"
        assert result["vault_url"] == "https://my-vault.vault.azure.net/"
        assert result["secret_name"] == "new-secret"
        assert result["secret_value"] == "new_secret_value"
        assert result["action"] == "create"

        # Verify mock calls
        mock_secret_client.set_secret.assert_called_once_with(
            "new-secret", "new_secret_value"
        )

    @patch("automax.plugins.azure_key_vault.ClientSecretCredential")
    @patch("automax.plugins.azure_key_vault.SecretClient")
    def test_azure_key_vault_plugin_with_service_principal(
        self, mock_client, mock_credential_class
    ):
        """
        Test azure_key_vault plugin execution with service principal authentication.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client
        mock_credential = MagicMock()
        mock_credential_class.return_value = mock_credential

        mock_secret = MagicMock()
        mock_secret.value = "my_azure_secret"
        mock_secret.properties.version = "v1"
        mock_secret.properties.enabled = True
        mock_secret.properties.expires_on = None
        mock_secret_client.get_secret.return_value = mock_secret

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "my-secret",
                "action": "read",
                "tenant_id": "tenant-123",
                "client_id": "client-456",
                "client_secret": "secret-789",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["secret_value"] == "my_azure_secret"

        # Verify mock calls
        mock_credential_class.assert_called_once_with(
            "tenant-123", "client-456", "secret-789"
        )
        mock_client.assert_called_once_with(
            vault_url="https://my-vault.vault.azure.net/", credential=mock_credential
        )

    @patch("automax.plugins.azure_key_vault.SecretClient")
    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_key_vault_plugin_secret_not_found(
        self, mock_credential, mock_client
    ):
        """
        Test azure_key_vault plugin execution with secret not found.
        """
        # Setup mocks
        mock_secret_client = MagicMock()
        mock_client.return_value = mock_secret_client
        mock_credential.return_value = MagicMock()

        mock_secret_client.get_secret.side_effect = Exception("Secret not found")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "nonexistent-secret",
                "action": "read",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Secret not found" in str(exc_info.value)

    def test_azure_key_vault_plugin_write_missing_value(self):
        """
        Test azure_key_vault plugin write action with missing value.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "new-secret",
                "action": "write",
                # Missing 'value' parameter
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Missing 'value' for write/create action" in str(exc_info.value)

    def test_azure_key_vault_plugin_invalid_action(self):
        """
        Test azure_key_vault plugin with invalid action.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "my-secret",
                "action": "invalid_action",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Invalid action" in str(exc_info.value)

    @patch("automax.plugins.azure_key_vault.DefaultAzureCredential")
    def test_azure_key_vault_plugin_credential_error(self, mock_credential):
        """
        Test azure_key_vault plugin with credential error.
        """
        # Setup mock to raise exception
        mock_credential.side_effect = Exception("Credential error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("azure_key_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://my-vault.vault.azure.net/",
                "secret_name": "my-secret",
                "action": "read",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Failed to get Azure credential" in str(exc_info.value)
