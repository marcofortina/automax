"""
Tests for the check_network_connection utility using the PluginManager class.
"""

import pytest

from automax.core.exceptions import AutomaxError


def test_check_network_connection_success(logger, plugin_manager):
    """Verify that a valid host and port return True."""
    check_network_connection = plugin_manager.get_plugin("check_network_connection")

    assert check_network_connection("example.com", 80, logger=logger)


def test_check_network_connection_failure(logger, plugin_manager):
    """Verify that invalid hosts raise AutomaxError."""
    check_network_connection = plugin_manager.get_plugin("check_network_connection")

    with pytest.raises(AutomaxError):
        check_network_connection("invalid-host.example", 9999, fail_fast=True)


def test_schema_loaded(plugin_manager):
    """Verify SCHEMA is loaded."""
    schema = plugin_manager.get_schema("check_network_connection")
    assert "host" in schema
