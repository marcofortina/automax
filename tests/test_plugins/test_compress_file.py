"""
Tests for compress_file plugin.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestCompressFilePlugin:
    """
    Test suite for compress_file plugin.
    """

    def test_compress_file_plugin_registered(self):
        """
        Verify that compress_file plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "compress_file" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("compress_file")
        assert metadata.name == "compress_file"
        assert metadata.version == "2.0.0"
        assert "compress" in metadata.tags
        assert "source_path" in metadata.required_config
        assert "output_path" in metadata.required_config
        assert "format" in metadata.optional_config

    def test_compress_file_plugin_instantiation(self):
        """
        Verify compress_file plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("compress_file")
        config = {
            "source_path": "/path/to/source",
            "output_path": "/path/to/output.gz",
            "format": "gzip",
            "compression_level": 6,
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_compress_file_plugin_configuration_validation(self):
        """
        Verify compress_file plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("compress_file")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"source_path": "/path"})  # missing output_path
        assert "required configuration" in str(exc_info.value).lower()

    @patch("automax.plugins.compress_file.gzip.open")
    @patch("automax.plugins.compress_file.open")
    @patch("automax.plugins.compress_file.shutil.copyfileobj")
    def test_compress_file_plugin_gzip_success(
        self, mock_copyfileobj, mock_open, mock_gzip_open
    ):
        """
        Test compress_file plugin execution with gzip format.
        """
        # Setup mocks per i file
        mock_source_file = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_source_file)
        mock_open.return_value.__exit__ = MagicMock(return_value=None)

        mock_gzip_file = MagicMock()
        mock_gzip_open.return_value.__enter__ = MagicMock(return_value=mock_gzip_file)
        mock_gzip_open.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("compress_file")

        # Mock completo dei Path objects
        with patch("automax.plugins.compress_file.Path") as MockPath:
            # Mock source path
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = True
            mock_source.is_dir.return_value = False
            mock_source.stat.return_value.st_size = 1000
            mock_source.__str__ = lambda self: "/path/to/source.txt"

            # Mock output path
            mock_output = MagicMock()
            mock_output.stat.return_value.st_size = 500
            mock_output.__str__ = lambda self: "/path/to/output.gz"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/source.txt":
                    return mock_source
                elif path_str == "/path/to/output.gz":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            plugin = plugin_class(
                {
                    "source_path": "/path/to/source.txt",
                    "output_path": "/path/to/output.gz",
                    "format": "gzip",
                    "compression_level": 6,
                }
            )

            result = plugin.execute()

            assert result["status"] == "success"
            assert result["source_path"] == "/path/to/source.txt"
            assert result["output_path"] == "/path/to/output.gz"
            assert result["format"] == "gzip"
            assert result["original_size"] == 1000
            assert result["compressed_size"] == 500

    @patch("automax.plugins.compress_file.tarfile.open")
    def test_compress_file_plugin_tar_success(self, mock_tarfile_open):
        """
        Test compress_file plugin execution with tar format.
        """
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__ = MagicMock(return_value=mock_tar)
        mock_tarfile_open.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("compress_file")

        with patch("automax.plugins.compress_file.Path") as MockPath:
            # Mock source path (directory)
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = False
            mock_source.is_dir.return_value = True
            mock_source.name = "source"
            mock_source.__str__ = lambda self: "/path/to/source"

            # Mock output path
            mock_output = MagicMock()
            mock_output.stat.return_value.st_size = 800
            mock_output.__str__ = lambda self: "/path/to/output.tar"
            mock_output.suffix = ".tar"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/source":
                    return mock_source
                elif path_str == "/path/to/output.tar":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            plugin = plugin_class(
                {
                    "source_path": "/path/to/source",
                    "output_path": "/path/to/output.tar",
                    "format": "tar",
                }
            )

            with patch.object(plugin, "_get_total_size", return_value=1000):
                result = plugin.execute()

            assert result["status"] == "success"
            assert result["format"] == "tar"
            assert result["original_size"] == 1000
            assert result["compressed_size"] == 800

    def test_compress_file_plugin_source_not_found(self):
        """
        Test compress_file plugin with non-existent source.
        """
        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("compress_file")
        plugin = plugin_class(
            {"source_path": "/path/to/nonexistent", "output_path": "/path/to/output.gz"}
        )

        with patch("automax.plugins.compress_file.Path") as MockPath:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            MockPath.return_value = mock_path

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Source path does not exist" in str(exc_info.value)

    def test_compress_file_plugin_unsupported_format(self):
        """
        Test compress_file plugin with unsupported format.
        """
        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("compress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/source",
                "output_path": "/path/to/output.xyz",
                "format": "unsupported",
            }
        )

        with patch("automax.plugins.compress_file.Path") as MockPath:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            MockPath.return_value = mock_path

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Unsupported compression format" in str(exc_info.value)

    @patch("automax.plugins.compress_file.zipfile.ZipFile")
    def test_compress_file_plugin_zip_success(self, mock_zipfile):
        """
        Test compress_file plugin execution with zip format.
        """
        # Setup mocks
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__ = MagicMock(return_value=mock_zip)
        mock_zipfile.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("compress_file")

        with patch("automax.plugins.compress_file.Path") as MockPath:
            # Mock source path (directory)
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = False
            mock_source.is_dir.return_value = True
            mock_source.name = "source"
            mock_source.__str__ = lambda self: "/path/to/source"

            # Mock output path
            mock_output = MagicMock()
            mock_output.stat.return_value.st_size = 600
            mock_output.__str__ = lambda self: "/path/to/output.zip"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/source":
                    return mock_source
                elif path_str == "/path/to/output.zip":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            plugin = plugin_class(
                {
                    "source_path": "/path/to/source",
                    "output_path": "/path/to/output.zip",
                    "format": "zip",
                }
            )

            with patch.object(plugin, "_get_total_size", return_value=1000):
                result = plugin.execute()

            assert result["status"] == "success"
            assert result["source_path"] == "/path/to/source"
            assert result["output_path"] == "/path/to/output.zip"
            assert result["format"] == "zip"
            assert result["original_size"] == 1000
            assert result["compressed_size"] == 600


class TestCompressFileErrorHandling:
    """
    Additional test suite for Compress File error scenarios.

    These tests complement the existing tests without modifying them.

    """

    def test_compress_file_plugin_source_not_directory_or_file(self):
        """
        Test compress_file plugin execution with source that is neither directory nor
        file.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("compress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/source",
                "output_path": "/path/to/output.gz",
            }
        )

        with patch("automax.plugins.compress_file.Path") as MockPath:
            # Mock source path
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = False
            mock_source.is_dir.return_value = False
            mock_source.__str__ = lambda self: "/path/to/source"

            # Mock output path
            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/output.gz"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/source":
                    return mock_source
                elif path_str == "/path/to/output.gz":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Source path is neither a file nor a directory" in str(
                exc_info.value
            )

    @patch("automax.plugins.compress_file.gzip.open")
    @patch("automax.plugins.compress_file.open")
    def test_compress_file_plugin_gzip_compression_error(
        self, mock_open, mock_gzip_open
    ):
        """
        Test compress_file plugin execution with gzip compression error.
        """
        # Setup mocks
        mock_gzip_open.side_effect = Exception("Compression error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("compress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/source.txt",
                "output_path": "/path/to/output.gz",
                "format": "gzip",
            }
        )

        with patch("automax.plugins.compress_file.Path") as MockPath:
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = True
            mock_source.is_dir.return_value = False
            mock_source.__str__ = lambda self: "/path/to/source.txt"

            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/output.gz"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/source.txt":
                    return mock_source
                elif path_str == "/path/to/output.gz":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Compression error" in str(exc_info.value)

    @patch("automax.plugins.compress_file.tarfile.open")
    def test_compress_file_plugin_tar_compression_error(self, mock_tarfile_open):
        """
        Test compress_file plugin execution with tar compression error.
        """
        # Setup mocks
        mock_tarfile_open.side_effect = Exception("Tar compression error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("compress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/source",
                "output_path": "/path/to/output.tar",
                "format": "tar",
            }
        )

        with patch("automax.plugins.compress_file.Path") as MockPath:
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = False
            mock_source.is_dir.return_value = True
            mock_source.__str__ = lambda self: "/path/to/source"

            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/output.tar"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/source":
                    return mock_source
                elif path_str == "/path/to/output.tar":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Tar compression error" in str(exc_info.value)

    @patch("automax.plugins.compress_file.zipfile.ZipFile")
    def test_compress_file_plugin_zip_compression_error(self, mock_zipfile):
        """
        Test compress_file plugin execution with zip compression error.
        """
        # Setup mocks
        mock_zipfile.side_effect = Exception("Zip compression error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("compress_file")
        plugin = plugin_class(
            {
                "source_path": "/path/to/source",
                "output_path": "/path/to/output.zip",
                "format": "zip",
            }
        )

        with patch("automax.plugins.compress_file.Path") as MockPath:
            mock_source = MagicMock()
            mock_source.exists.return_value = True
            mock_source.is_file.return_value = False
            mock_source.is_dir.return_value = True
            mock_source.__str__ = lambda self: "/path/to/source"

            mock_output = MagicMock()
            mock_output.__str__ = lambda self: "/path/to/output.zip"
            mock_output.parent = MagicMock()

            def path_side_effect(path_str):
                if path_str == "/path/to/source":
                    return mock_source
                elif path_str == "/path/to/output.zip":
                    return mock_output
                return MagicMock()

            MockPath.side_effect = path_side_effect

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "Zip compression error" in str(exc_info.value)
