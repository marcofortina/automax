"""
Tests for check_tcp_connection plugin.
"""

import socket
from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestCheckTcpConnectionPlugin:
    """
    Test suite for check_tcp_connection plugin.
    """

    def test_check_tcp_plugin_registered(self):
        """
        Verify that check_tcp_connection plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "check_tcp_connection" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("check_tcp_connection")
        assert metadata.name == "check_tcp_connection"
        assert metadata.version == "2.0.0"
        assert "network" in metadata.tags
        assert "host" in metadata.required_config
        assert "port" in metadata.required_config

    def test_check_tcp_plugin_instantiation(self):
        """
        Verify check_tcp_connection plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
        config = {"host": "example.com", "port": 80, "timeout": 5, "fail_fast": True}

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_check_tcp_plugin_configuration_validation(self):
        """
        Verify check_tcp_connection plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("socket.create_connection")
    def test_check_tcp_plugin_execution_success(self, mock_create_connection):
        """
        Test check_tcp_connection plugin execution with successful connection.
        """
        # Setup mock
        mock_connection = MagicMock()
        mock_create_connection.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_create_connection.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
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
    def test_check_tcp_plugin_execution_failure(self, mock_create_connection):
        """
        Test check_tcp_connection plugin execution with connection failure.
        """
        # Setup mock to raise exception
        mock_create_connection.side_effect = Exception("Connection refused")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
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
    def test_check_tcp_plugin_execution_fail_fast(self, mock_create_connection):
        """
        Test check_tcp_connection plugin execution with fail_fast=True.
        """
        # Setup mock to raise exception
        mock_create_connection.side_effect = Exception("Connection refused")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
        plugin = plugin_class(
            {"host": "example.com", "port": 80, "timeout": 5, "fail_fast": True}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "TCP connection to example.com:80 failed" in str(exc_info.value)


class TestCheckTCPConnectionErrorHandling:
    """
    Additional test suite for Check TCP Connection error scenarios.

    These tests complement the existing tests without modifying them.

    """

    @patch("socket.create_connection")
    def test_check_tcp_connection_plugin_dns_resolution_error(
        self, mock_create_connection
    ):
        """
        Test check_tcp_connection plugin execution with DNS resolution error.
        """
        # Setup mock to raise DNS error
        mock_create_connection.side_effect = socket.gaierror(
            "Name or service not known"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
        plugin = plugin_class(
            {"host": "invalid-hostname", "port": 80, "fail_fast": False}
        )

        result = plugin.execute()

        assert result["status"] == "failure"
        assert result["connected"] is False
        assert "error" in result

    @patch("socket.create_connection")
    def test_check_tcp_connection_plugin_connection_aborted(
        self, mock_create_connection
    ):
        """
        Test check_tcp_connection plugin execution with connection aborted.
        """
        # Setup mock to raise connection aborted error
        mock_create_connection.side_effect = ConnectionAbortedError(
            "Connection aborted"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
        plugin = plugin_class({"host": "example.com", "port": 80, "fail_fast": False})

        result = plugin.execute()

        assert result["status"] == "failure"
        assert result["connected"] is False
        assert "error" in result

    @patch("socket.create_connection")
    def test_check_tcp_connection_plugin_connection_reset(self, mock_create_connection):
        """
        Test check_tcp_connection plugin execution with connection reset.
        """
        # Setup mock to raise connection reset error
        mock_create_connection.side_effect = ConnectionResetError(
            "Connection reset by peer"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
        plugin = plugin_class({"host": "example.com", "port": 80, "fail_fast": False})

        result = plugin.execute()

        assert result["status"] == "failure"
        assert result["connected"] is False
        assert "error" in result

    @patch("socket.create_connection")
    def test_check_tcp_connection_plugin_socket_error(self, mock_create_connection):
        """
        Test check_tcp_connection plugin execution with general socket error.
        """
        # Setup mock to raise socket error
        mock_create_connection.side_effect = socket.error("Socket error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_tcp_connection")
        plugin = plugin_class({"host": "example.com", "port": 80, "fail_fast": False})

        result = plugin.execute()

        assert result["status"] == "failure"
        assert result["connected"] is False
        assert "error" in result
