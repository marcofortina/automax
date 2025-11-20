"""
Tests for write_file_content plugin.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestWriteFileContentPlugin:
    """
    Test suite for write_file_content plugin.
    """

    def test_write_file_plugin_registered(self):
        """
        Verify that write_file_content plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "write_file_content" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("write_file_content")
        assert metadata.name == "write_file_content"
        assert metadata.version == "2.0.0"
        assert "file" in metadata.tags
        assert "file_path" in metadata.required_config
        assert "content" in metadata.required_config

    def test_write_file_plugin_instantiation(self):
        """
        Verify write_file_content plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")
        config = {"file_path": "test.txt", "content": "test content"}

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_write_file_plugin_configuration_validation(self):
        """
        Verify write_file_content plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_write_file_plugin_execution(
        self, mock_stat, mock_exists, mock_open, mock_mkdir
    ):
        """
        Test write_file_content plugin execution with mocked operations.
        """
        # Setup mocks
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 12
        mock_file = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_open.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")
        plugin = plugin_class(
            {
                "file_path": "test.txt",
                "content": "test content",
                "encoding": "utf-8",
                "mode": "w",
                "create_dirs": True,
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["file_path"] == "test.txt"
        assert result["content_length"] == len("test content")
        assert result["file_size"] == 12
        assert result["encoding"] == "utf-8"
        assert result["mode"] == "w"
        assert result["create_dirs"] is True
        assert result["status"] == "success"

        # Verify mock calls
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_open.assert_called_once_with(Path("test.txt"), "w", encoding="utf-8")
        mock_file.write.assert_called_once_with("test content")

    def test_write_file_plugin_invalid_mode(self):
        """
        Test write_file_content plugin with invalid mode.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")
        plugin = plugin_class(
            {"file_path": "test.txt", "content": "test content", "mode": "invalid_mode"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "invalid file mode" in str(exc_info.value).lower()


class TestWriteFileContentErrorHandling:
    """
    Additional test suite for Write File Content error scenarios.

    These tests complement the existing tests without modifying them.

    """

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_write_file_content_plugin_permission_denied(self, mock_open, mock_mkdir):
        """
        Test write_file_content plugin execution with permission denied.
        """
        # Setup mocks
        mock_mkdir.side_effect = PermissionError("Permission denied")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")
        plugin = plugin_class({"file_path": "/root/file.txt", "content": "test"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Permission denied" in str(exc_info.value)

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_write_file_content_plugin_disk_full(self, mock_open, mock_mkdir):
        """
        Test write_file_content plugin execution with disk full.
        """
        # Setup mocks
        mock_open.side_effect = OSError("No space left on device")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")
        plugin = plugin_class({"file_path": "file.txt", "content": "test"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "No space left on device" in str(exc_info.value)

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_write_file_content_plugin_invalid_encoding(self, mock_open, mock_mkdir):
        """
        Test write_file_content plugin execution with invalid encoding.
        """
        # Setup mocks
        mock_file = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_open.return_value.__exit__ = MagicMock(return_value=None)
        mock_file.write.side_effect = UnicodeEncodeError(
            "utf-8", "test", 0, 1, "Invalid character"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")
        plugin = plugin_class(
            {"file_path": "file.txt", "content": "test", "encoding": "utf-8"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Encoding error" in str(exc_info.value)

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_write_file_content_plugin_read_only_filesystem(
        self, mock_open, mock_mkdir
    ):
        """
        Test write_file_content plugin execution with read-only filesystem.
        """
        # Setup mocks
        mock_open.side_effect = OSError("Read-only file system")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("write_file_content")
        plugin = plugin_class({"file_path": "/rofs/file.txt", "content": "test"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Read-only file system" in str(exc_info.value)
