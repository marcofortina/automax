"""
Tests for read_file_content plugin.
"""

from unittest.mock import patch

import pytest

from automax.plugins.registry import global_registry


class TestReadFileContentPlugin:
    """
    Test suite for read_file_content plugin.
    """

    def test_read_file_plugin_registered(self):
        """
        Verify that read_file_content plugin is properly registered.
        """
        global_registry.load_all_plugins()

        # Check plugin is registered
        assert "read_file_content" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("read_file_content")
        assert metadata.name == "read_file_content"
        assert metadata.version == "2.0.0"
        assert "file" in metadata.tags
        assert "file_path" in metadata.required_config

    def test_read_file_plugin_instantiation(self):
        """
        Verify read_file_content plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("read_file_content")
        config = {
            "file_path": "/tmp/test_file.txt",
            "encoding": "utf-8",
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_read_file_plugin_configuration_validation(self):
        """
        Verify read_file_content plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("read_file_content")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"vault_url": "https://vault.azure.net/"})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_read_file_plugin_execution(
        self, mock_is_file, mock_exists, mock_read_text
    ):
        """
        Test read_file_content plugin execution with mocked file operations.
        """
        global_registry.load_all_plugins()

        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_read_text.return_value = "test file content"

        plugin_class = global_registry.get_plugin_class("read_file_content")
        plugin = plugin_class({"file_path": "test.txt", "encoding": "utf-8"})

        result = plugin.execute()

        # Verify result structure
        assert result["file_path"] == "test.txt"
        assert result["content"] == "test file content"
        assert result["encoding"] == "utf-8"
        assert result["size"] == len("test file content")
        assert result["status"] == "success"

        # Verify mock calls
        mock_exists.assert_called_once()
        mock_is_file.assert_called_once()
        mock_read_text.assert_called_once_with(encoding="utf-8")
