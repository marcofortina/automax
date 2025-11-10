"""
Tests for the run_http_request utility.
"""

import pytest

from automax.core.exceptions import AutomaxError


def test_run_http_request_success(logger, plugin_manager):
    """Verify that HTTP requests return valid responses."""
    run_http_request = plugin_manager.get_plugin("run_http_request")
    response = run_http_request("https://example.com", logger=logger, dry_run=True)
    assert response == "Dry-run response"
    # Real test (assume success)
    response = run_http_request("https://example.com")
    assert "Example Domain" in response


def test_run_http_request_failure(logger, plugin_manager):
    """Verify that HTTP requests to invalid URLs raise AutomaxError."""
    run_http_request = plugin_manager.get_plugin("run_http_request")
    with pytest.raises(AutomaxError):
        run_http_request("https://invalid-url.example", fail_fast=True)


def test_schema_loaded(plugin_manager):
    """Verify SCHEMA is loaded."""
    schema = plugin_manager.get_schema("run_http_request")
    assert "url" in schema
