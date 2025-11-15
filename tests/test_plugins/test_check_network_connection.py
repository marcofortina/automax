"""
Tests for check_network_connection plugin.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestCheckNetworkConnectionPlugin:
    """
    Test suite for check_network_connection plugin.
    """

    def test_check_network_plugin_registered(self):
        """
        Verify that check_network_connection plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "check_network_connection" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("check_network_connection")
        assert metadata.name == "check_network_connection"
        assert metadata.version == "2.0.0"
        assert "network" in metadata.tags
        assert "host" in metadata.required_config
        assert "port" in metadata.optional_config

    def test_check_network_plugin_instantiation(self):
        """
        Verify check_network_connection plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_network_connection")
        config = {"host": "example.com", "port": 80, "timeout": 5, "fail_fast": True}

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_check_network_plugin_configuration_validation(self):
        """
        Verify check_network_connection plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_network_connection")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("socket.create_connection")
    def test_check_network_plugin_execution_success(self, mock_create_connection):
        """
        Test check_network_connection plugin execution with successful connection.
        """
        # Setup mock
        mock_connection = MagicMock()
        mock_create_connection.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_create_connection.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_network_connection")
        plugin = plugin_class(
            {"host": "example.com", "port": 80, "timeout": 5, "fail_fast": True}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["host"] == "example.com"
        assert result["port"] == 80
        assert result["timeout"] == 5
        assert result["connected"] is True

        # Verify mock call
        mock_create_connection.assert_called_once_with(("example.com", 80), timeout=5)

    @patch("socket.create_connection")
    def test_check_network_plugin_execution_failure(self, mock_create_connection):
        """
        Test check_network_connection plugin execution with connection failure.
        """
        # Setup mock to raise exception
        mock_create_connection.side_effect = Exception("Connection refused")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_network_connection")
        plugin = plugin_class(
            {"host": "example.com", "port": 80, "timeout": 5, "fail_fast": False}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "failure"
        assert result["host"] == "example.com"
        assert result["port"] == 80
        assert result["timeout"] == 5
        assert result["connected"] is False
        assert "error" in result

    @patch("socket.create_connection")
    def test_check_network_plugin_execution_fail_fast(self, mock_create_connection):
        """
        Test check_network_connection plugin execution with fail_fast=True.
        """
        # Setup mock to raise exception
        mock_create_connection.side_effect = Exception("Connection refused")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_network_connection")
        plugin = plugin_class(
            {"host": "example.com", "port": 80, "timeout": 5, "fail_fast": True}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Connection to example.com:80 failed" in str(exc_info.value)
