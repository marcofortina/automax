"""
Tests for hashicorp_vault plugin.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

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

        # Verify metadata
        metadata = global_registry.get_metadata("hashicorp_vault")
        assert metadata.name == "hashicorp_vault"
        assert "vault" in metadata.tags
        assert "vault_url" in metadata.required_config
        assert "secret_path" in metadata.required_config

    def test_hashicorp_vault_plugin_instantiation(self):
        """
        Verify hashicorp_vault plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        config = {
            "vault_url": "https://vault.example.com",
            "secret_path": "secret/my-app",
            "token": "s.1234567890",
            "timeout": 60,
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
            plugin_class({"vault_url": "https://vault.example.com"})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("requests.get")
    def test_hashicorp_vault_plugin_execution_success(self, mock_get):
        """
        Test hashicorp_vault plugin execution with successful secret retrieval.
        """
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"data": {"username": "admin", "password": "secret123"}}
        }
        mock_get.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://vault.example.com",
                "secret_path": "secret/my-app",
                "token": "s.1234567890",
                "engine": "secret",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["vault_url"] == "https://vault.example.com"
        assert result["secret_path"] == "secret/my-app"
        assert result["secret_data"] == {"username": "admin", "password": "secret123"}

        # Verify mock call
        mock_get.assert_called_once_with(
            "https://vault.example.com/v1/secret/data/secret/my-app",
            headers={"X-Vault-Token": "s.1234567890"},
            timeout=30,
        )

    @patch("requests.get")
    def test_hashicorp_vault_plugin_custom_engine(self, mock_get):
        """
        Test hashicorp_vault plugin execution with custom secrets engine.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"data": {"api_key": "abc123"}}}
        mock_get.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://vault.example.com",
                "secret_path": "my-app",
                "token": "s.1234567890",
                "engine": "kv",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["engine"] == "kv"

        # Verify mock call
        mock_get.assert_called_once_with(
            "https://vault.example.com/v1/kv/data/my-app",
            headers={"X-Vault-Token": "s.1234567890"},
            timeout=30,
        )

    @patch("requests.get")
    def test_hashicorp_vault_plugin_request_failure(self, mock_get):
        """
        Test hashicorp_vault plugin execution with request failure.
        """
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://vault.example.com",
                "secret_path": "secret/my-app",
                "token": "s.1234567890",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Vault request failed" in str(exc_info.value)

    @patch("requests.get")
    def test_hashicorp_vault_plugin_http_error(self, mock_get):
        """
        Test hashicorp_vault plugin execution with HTTP error.
        """
        # Setup mock to raise exception
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "403 Client Error"
        )
        mock_get.return_value = mock_response

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://vault.example.com",
                "secret_path": "secret/my-app",
                "token": "s.1234567890",
            }
        )

        # Test with missing required configuration
        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Vault request failed" in str(exc_info.value)

    def test_hashicorp_vault_plugin_missing_token(self):
        """
        Test hashicorp_vault plugin execution with missing token.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("hashicorp_vault")
        plugin = plugin_class(
            {
                "vault_url": "https://vault.example.com",
                "secret_path": "secret/my-app",
                # missing token
            }
        )

        # Test with missing required configuration
        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Vault token is required" in str(exc_info.value)
