"""
Tests for the read_file_content utility.
"""

import pytest

from automax.core.exceptions import AutomaxError


def test_read_file_content_success(tmp_path, logger, plugin_manager):
    """
    Verify that reading file content returns expected text.
    """
    file = tmp_path / "test.txt"
    file.write_text("content")
    read_file_content = plugin_manager.get_plugin("read_file_content")
    content = read_file_content(str(file), logger=logger)
    assert content == "content"


def test_read_file_content_failure(logger, plugin_manager):
    """
    Verify that reading a non-existent file raises AutomaxError.
    """
    read_file_content = plugin_manager.get_plugin("read_file_content")
    with pytest.raises(AutomaxError):
        read_file_content("/nonexistent", fail_fast=True)


def test_schema_loaded(plugin_manager):
    """
    Verify SCHEMA is loaded.
    """
    schema = plugin_manager.get_schema("read_file_content")
    assert "file_path" in schema
