"""
Tests for uncompress_file plugin.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestUncompressFilePlugin:
    """
    Test suite for uncompress_file plugin.
    """

    def test_uncompress_file_plugin_registered(self):
        """
        Verify that uncompress_file plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "uncompress_file" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("uncompress_file")
        assert metadata.name == "uncompress_file"
        assert metadata.version == "2.0.0"
        assert "uncompress" in metadata.tags
        assert "source_path" in metadata.required_config
        assert "output_path" in metadata.required_config
        assert "format" in metadata.optional_config

    def test_uncompress_file_plugin_instantiation(self):
        """
        Verify uncompress_file plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("uncompress_file")
        config = {
            "source_path": "/path/to/archive.gz",
            "output_path": "/path/to/extracted",
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_uncompress_file_plugin_configuration_validation(self):
        """
        Verify uncompress_file plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("uncompress_file")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"source_path": "/path"})  # missing output_path
        assert "required configuration" in str(exc_info.value).lower()

    @patch("automax.plugins.uncompress_file.gzip.open")
    @patch("automax.plugins.uncompress_file.open")
    @patch("automax.plugins.uncompress_file.shutil.copyfileobj")
    def test_uncompress_file_plugin_gzip_success(
        self, mock_copyfileobj, mock_open, mock_gzip_open
    ):
        """
        Test uncompress_file plugin execution with gzip format.
        """
        # Setup mocks
        mock_gzip_file = MagicMock()
        mock_gzip_open.return_value.__enter__ = MagicMock(return_value=mock_gzip_file)
        mock_gzip_open.return_value.__exit__ = MagicMock(return_value=None)

        mock_output_file = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_output_file)
        mock_open.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("uncompress_file")

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            # Mock source path
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.stat.return_value.st_size = 500
            mock_source.name = "archive.gz"
            mock_source.__str__ = lambda self: "/path/to/archive.gz"

            # Mock output path
            mock_output = MagicMock()
            mock_output.stat.return_value.st_size = 1000
            mock_output.__str__ = lambda self: "/path/to/extracted/file.txt"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/archive.gz":
                    return mock_source
                elif path_str == "/path/to/extracted/file.txt":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            plugin = plugin_class(
                {
                    "source_path": "/path/to/archive.gz",
                    "output_path": "/path/to/extracted/file.txt",
                    "format": "gzip",
                }
            )

            result = plugin.execute()

            assert result["status"] == "success"
            assert result["source_path"] == "/path/to/archive.gz"
            assert result["output_path"] == "/path/to/extracted/file.txt"
            assert result["format"] == "gzip"
            assert result["compressed_size"] == 500
            assert result["extracted_size"] == 1000

    @patch("automax.plugins.uncompress_file.tarfile.open")
    def test_uncompress_file_plugin_tar_success(self, mock_tarfile_open):
        """
        Test uncompress_file plugin execution with tar format.
        """
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__ = MagicMock(return_value=mock_tar)
        mock_tarfile_open.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("uncompress_file")

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            # Mock source path
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.name = "archive.tar"
            mock_source.__str__ = lambda self: "/path/to/archive.tar"

            # Mock output path
            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/extracted"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/archive.tar":
                    return mock_source
                elif path_str == "/path/to/extracted":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            plugin = plugin_class(
                {
                    "source_path": "/path/to/archive.tar",
                    "output_path": "/path/to/extracted",
                    "format": "tar",
                }
            )

            result = plugin.execute()

            assert result["status"] == "success"
            assert result["source_path"] == "/path/to/archive.tar"
            assert result["output_path"] == "/path/to/extracted"
            assert result["format"] == "tar"

    @patch("automax.plugins.uncompress_file.zipfile.ZipFile")
    def test_uncompress_file_plugin_zip_success(self, mock_zipfile):
        """
        Test uncompress_file plugin execution with zip format.
        """
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__ = MagicMock(return_value=mock_zip)
        mock_zipfile.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("uncompress_file")

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            # Mock source path
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.stat.return_value.st_size = 500
            mock_source.name = "archive.zip"
            mock_source.__str__ = lambda self: "/path/to/archive.zip"

            # Mock output path
            mock_output = MagicMock()
            mock_output.stat.return_value.st_size = 1000
            mock_output.__str__ = lambda self: "/path/to/extracted"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/archive.zip":
                    return mock_source
                elif path_str == "/path/to/extracted":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            plugin = plugin_class(
                {
                    "source_path": "/path/to/archive.zip",
                    "output_path": "/path/to/extracted",
                    "format": "zip",
                }
            )

            result = plugin.execute()

            assert result["status"] == "success"
            assert result["source_path"] == "/path/to/archive.zip"
            assert result["output_path"] == "/path/to/extracted"
            assert result["format"] == "zip"
            assert result["compressed_size"] == 500
            assert result["extracted_size"] == 1000

    def test_uncompress_file_plugin_source_not_found(self):
        """
        Test uncompress_file plugin with non-existent source.
        """
        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("uncompress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/nonexistent.gz",
                "output_path": "/path/to/extracted",
            }
        )

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            MockPath.return_value = mock_path

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Source path does not exist" in str(exc_info.value)

    def test_uncompress_file_plugin_unsupported_format(self):
        """
        Test uncompress_file plugin with unsupported format.
        """
        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("uncompress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/source.xyz",
                "output_path": "/path/to/output",
                "format": "unsupported",
            }
        )

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            MockPath.return_value = mock_path

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Unsupported compression format" in str(exc_info.value)


class TestUncompressFileErrorHandling:
    """
    Additional test suite for Uncompress File error scenarios.

    These tests complement the existing tests without modifying them.

    """

    @patch("automax.plugins.uncompress_file.gzip.open")
    @patch("automax.plugins.uncompress_file.open")
    def test_uncompress_file_plugin_gzip_decompression_error(
        self, mock_open, mock_gzip_open
    ):
        """
        Test uncompress_file plugin execution with gzip decompression error.
        """
        # Setup mocks
        mock_gzip_open.side_effect = Exception("Decompression error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("uncompress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/archive.gz",
                "output_path": "/path/to/extracted",
                "format": "gzip",
            }
        )

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.__str__ = lambda self: "/path/to/archive.gz"

            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/extracted"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/archive.gz":
                    return mock_source
                elif path_str == "/path/to/extracted":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Decompression error" in str(exc_info.value)

    @patch("automax.plugins.uncompress_file.tarfile.open")
    def test_uncompress_file_plugin_tar_decompression_error(self, mock_tarfile_open):
        """
        Test uncompress_file plugin execution with tar decompression error.
        """
        # Setup mocks
        mock_tarfile_open.side_effect = Exception("Tar decompression error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("uncompress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/archive.tar",
                "output_path": "/path/to/extracted",
                "format": "tar",
            }
        )

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.__str__ = lambda self: "/path/to/archive.tar"

            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/extracted"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/archive.tar":
                    return mock_source
                elif path_str == "/path/to/extracted":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Tar decompression error" in str(exc_info.value)

    @patch("automax.plugins.uncompress_file.zipfile.ZipFile")
    def test_uncompress_file_plugin_zip_decompression_error(self, mock_zipfile):
        """
        Test uncompress_file plugin execution with zip decompression error.
        """
        # Setup mocks
        mock_zipfile.side_effect = Exception("Zip decompression error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("uncompress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/archive.zip",
                "output_path": "/path/to/extracted",
                "format": "zip",
            }
        )

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.__str__ = lambda self: "/path/to/archive.zip"

            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/extracted"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/archive.zip":
                    return mock_source
                elif path_str == "/path/to/extracted":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Zip decompression error" in str(exc_info.value)

    @patch("automax.plugins.uncompress_file.gzip.open")
    @patch("automax.plugins.uncompress_file.open")
    def test_uncompress_file_plugin_corrupted_archive(self, mock_open, mock_gzip_open):
        """
        Test uncompress_file plugin execution with corrupted archive.
        """
        # Setup mocks
        mock_gzip_file = MagicMock()
        mock_gzip_open.return_value.__enter__ = MagicMock(return_value=mock_gzip_file)
        mock_gzip_open.return_value.__exit__ = MagicMock(return_value=None)
        mock_gzip_file.read.side_effect = Exception("Corrupted archive")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("uncompress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/corrupted.gz",
                "output_path": "/path/to/extracted",
                "format": "gzip",
            }
        )

        with patch("automax.plugins.uncompress_file.Path") as MockPath:
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.__str__ = lambda self: "/path/to/corrupted.gz"

            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/extracted"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/corrupted.gz":
                    return mock_source
                elif path_str == "/path/to/extracted":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Corrupted archive" in str(exc_info.value)
