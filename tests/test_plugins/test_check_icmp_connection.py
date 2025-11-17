"""
Tests for check_icmp_connection plugin.
"""

from unittest.mock import patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestCheckIcmpConnectionPlugin:
    """
    Test suite for check_icmp_connection plugin.
    """

    def test_check_icmp_plugin_registered(self):
        """
        Verify that check_icmp_connection plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "check_icmp_connection" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("check_icmp_connection")
        assert metadata.name == "check_icmp_connection"
        assert metadata.version == "2.0.0"
        assert "network" in metadata.tags
        assert "host" in metadata.required_config
        assert "count" in metadata.optional_config

    def test_check_icmp_plugin_instantiation(self):
        """
        Verify check_icmp_connection plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")
        config = {"host": "example.com", "count": 4, "timeout": 2, "fail_fast": True}

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_check_icmp_plugin_configuration_validation(self):
        """
        Verify check_icmp_connection plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("automax.plugins.check_icmp_connection.verbose_ping")
    def test_check_icmp_plugin_execution_success(self, mock_verbose_ping):
        """
        Test check_icmp_connection plugin execution with successful ping.
        """
        # Setup mock - verbose_ping returns number of successful pings
        mock_verbose_ping.return_value = 4  # All 4 pings successful

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")
        plugin = plugin_class(
            {"host": "example.com", "count": 4, "timeout": 2, "fail_fast": True}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["host"] == "example.com"
        assert result["count"] == 4
        assert result["timeout"] == 2
        assert result["connected"] is True
        assert result["success_count"] == 4
        assert result["success_rate"] == 100.0

        # Verify mock call without checking the exact log_func
        mock_verbose_ping.assert_called_once()
        call_args = mock_verbose_ping.call_args
        assert call_args.kwargs["dest_addr"] == "example.com"
        assert call_args.kwargs["count"] == 4
        assert call_args.kwargs["timeout"] == 2
        assert call_args.kwargs["interval"] == 0.2
        assert callable(call_args.kwargs["log_func"])

    @patch("automax.plugins.check_icmp_connection.verbose_ping")
    def test_check_icmp_plugin_execution_failure(self, mock_verbose_ping):
        """
        Test check_icmp_connection plugin execution with ping failure.
        """
        # Setup mock - no successful pings
        mock_verbose_ping.return_value = 0

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")
        plugin = plugin_class(
            {"host": "example.com", "count": 4, "timeout": 2, "fail_fast": False}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "failure"
        assert result["host"] == "example.com"
        assert result["count"] == 4
        assert result["timeout"] == 2
        assert result["connected"] is False
        assert result["success_count"] == 0
        assert result["success_rate"] == 0.0
        assert "error" in result

        # Verify mock call
        mock_verbose_ping.assert_called_once()
        call_args = mock_verbose_ping.call_args
        assert call_args.kwargs["dest_addr"] == "example.com"
        assert call_args.kwargs["count"] == 4
        assert call_args.kwargs["timeout"] == 2
        assert call_args.kwargs["interval"] == 0.2
        assert callable(call_args.kwargs["log_func"])

    @patch("automax.plugins.check_icmp_connection.verbose_ping")
    def test_check_icmp_plugin_execution_fail_fast(self, mock_verbose_ping):
        """
        Test check_icmp_connection plugin execution with fail_fast=True.
        """
        # Setup mock - no successful pings
        mock_verbose_ping.return_value = 0

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")
        plugin = plugin_class(
            {"host": "example.com", "count": 4, "timeout": 2, "fail_fast": True}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "ICMP ping to example.com failed" in str(exc_info.value)

        # Verify mock call
        mock_verbose_ping.assert_called_once()
        call_args = mock_verbose_ping.call_args
        assert call_args.kwargs["dest_addr"] == "example.com"
        assert call_args.kwargs["count"] == 4
        assert call_args.kwargs["timeout"] == 2
        assert call_args.kwargs["interval"] == 0.2
        assert callable(call_args.kwargs["log_func"])

    @patch("automax.plugins.check_icmp_connection.verbose_ping")
    def test_check_icmp_plugin_execution_host_unknown(self, mock_verbose_ping):
        """
        Test check_icmp_connection plugin execution with host resolution error.
        """
        from ping3 import errors

        # Setup mock to raise host unknown error
        mock_verbose_ping.side_effect = errors.HostUnknown("Host not found")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")
        plugin = plugin_class(
            {"host": "invalid-host", "count": 4, "timeout": 2, "fail_fast": False}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "failure"
        assert result["host"] == "invalid-host"
        assert result["connected"] is False
        assert "error" in result
        assert "Host not found" in result["error"]

        # Verify mock call
        mock_verbose_ping.assert_called_once()
        call_args = mock_verbose_ping.call_args
        assert call_args.kwargs["dest_addr"] == "invalid-host"
        assert call_args.kwargs["count"] == 4
        assert call_args.kwargs["timeout"] == 2
        assert call_args.kwargs["interval"] == 0.2
        assert callable(call_args.kwargs["log_func"])

    @patch("automax.plugins.check_icmp_connection.verbose_ping")
    def test_check_icmp_plugin_execution_general_error(self, mock_verbose_ping):
        """
        Test check_icmp_connection plugin execution with general error.
        """
        # Setup mock to raise general exception
        mock_verbose_ping.side_effect = Exception("Network error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")
        plugin = plugin_class(
            {"host": "example.com", "count": 4, "timeout": 2, "fail_fast": False}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "failure"
        assert result["host"] == "example.com"
        assert result["connected"] is False
        assert "error" in result
        assert "Network error" in result["error"]

        # Verify mock call
        mock_verbose_ping.assert_called_once()
        call_args = mock_verbose_ping.call_args
        assert call_args.kwargs["dest_addr"] == "example.com"
        assert call_args.kwargs["count"] == 4
        assert call_args.kwargs["timeout"] == 2
        assert call_args.kwargs["interval"] == 0.2
        assert callable(call_args.kwargs["log_func"])
