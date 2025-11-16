"""
Tests for check_icmp_connection plugin.
"""

from unittest.mock import MagicMock, patch

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
        assert metadata.version == "1.0.0"
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

    @patch("automax.plugins.check_icmp_connection.icmp_ping")
    def test_check_icmp_plugin_execution_success(self, mock_ping):
        """
        Test check_icmp_connection plugin execution with successful ping.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.is_alive = True
        mock_result.packet_loss = 0.0
        mock_result.avg_rtt = 10.5
        mock_result.min_rtt = 8.2
        mock_result.max_rtt = 12.7
        mock_ping.return_value = mock_result

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
        assert result["packet_loss"] == 0.0
        assert result["rtt_avg_ms"] == 10.5
        assert result["rtt_min_ms"] == 8.2
        assert result["rtt_max_ms"] == 12.7
        assert result["success_rate"] == 100.0

        # Verify mock call - ORA INCLUDE privileged=False
        mock_ping.assert_called_once_with(
            address="example.com",
            count=4,
            timeout=2,
            interval=0.2,
            privileged=False,  # <=== AGGIUNTO
        )

    @patch("automax.plugins.check_icmp_connection.icmp_ping")
    def test_check_icmp_plugin_execution_failure(self, mock_ping):
        """
        Test check_icmp_connection plugin execution with ping failure.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.is_alive = False
        mock_result.packet_loss = 100.0
        mock_ping.return_value = mock_result

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
        assert result["packet_loss"] == 100.0
        assert result["success_rate"] == 0.0
        assert "error" in result

        # Verify mock call include privileged=False
        mock_ping.assert_called_once_with(
            address="example.com", count=4, timeout=2, interval=0.2, privileged=False
        )

    @patch("automax.plugins.check_icmp_connection.icmp_ping")
    def test_check_icmp_plugin_execution_fail_fast(self, mock_ping):
        """
        Test check_icmp_connection plugin execution with fail_fast=True.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.is_alive = False
        mock_result.packet_loss = 100.0
        mock_ping.return_value = mock_result

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("check_icmp_connection")
        plugin = plugin_class(
            {"host": "example.com", "count": 4, "timeout": 2, "fail_fast": True}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "ICMP ping to example.com failed" in str(exc_info.value)

        # Verify mock call include privileged=False
        mock_ping.assert_called_once_with(
            address="example.com", count=4, timeout=2, interval=0.2, privileged=False
        )

    @patch("automax.plugins.check_icmp_connection.icmp_ping")
    def test_check_icmp_plugin_execution_name_resolution_error(self, mock_ping):
        """
        Test check_icmp_connection plugin execution with name resolution error.
        """
        from icmplib import exceptions

        # Setup mock to raise name resolution error
        mock_ping.side_effect = exceptions.NameLookupError("Name or service not known")

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

        # Verify mock call include privileged=False
        mock_ping.assert_called_once_with(
            address="invalid-host", count=4, timeout=2, interval=0.2, privileged=False
        )

    @patch("automax.plugins.check_icmp_connection.icmp_ping")
    def test_check_icmp_plugin_execution_socket_error(self, mock_ping):
        """
        Test check_icmp_connection plugin execution with socket permission error.
        """
        from icmplib import exceptions

        # Setup mock to raise socket permission error
        mock_ping.side_effect = exceptions.SocketPermissionError(
            "Root privileges required"
        )

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
        assert "Root privileges" in result["error"]

        # Verify mock call include privileged=False
        mock_ping.assert_called_once_with(
            address="example.com", count=4, timeout=2, interval=0.2, privileged=False
        )
