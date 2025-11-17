"""
Base tests for plugin verification.
"""

from unittest.mock import patch

import pytest

from automax.core.managers.plugin_manager import PluginManager
from automax.plugins.registry import global_registry


class TestPluginBase:
    """
    Test suite for plugin verification.
    """

    def test_plugin_registry_loaded(self):
        """
        Verify that the plugin registry loads correctly.
        """
        global_registry.load_all_plugins()
        plugins = global_registry.list_plugins()

        # Should find at least the migrated read_file_content plugin
        assert len(plugins) >= 1, f"No plugins loaded in registry. Found: {plugins}"
        assert "read_file_content" in plugins

    def test_plugin_class_structure(self):
        """
        Verify plugin class structure and inheritance.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("read_file_content")

        # Verify class has required attributes
        assert hasattr(plugin_class, "execute")
        assert hasattr(plugin_class, "METADATA")
        assert hasattr(plugin_class, "validate")

        # Verify metadata structure
        metadata = plugin_class.METADATA
        assert metadata.name == "read_file_content"
        assert isinstance(metadata.tags, list)
        assert isinstance(metadata.required_config, list)
        assert isinstance(metadata.optional_config, list)

    def test_plugin_instantiation_with_config(self):
        """
        Verify plugins can be instantiated with configuration.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("read_file_content")

        # Create test configuration
        config = {"file_path": "test.txt", "encoding": "utf-8"}

        # Verify instantiation works
        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_plugin_configuration_validation(self):
        """
        Verify plugin configuration validation works.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("read_file_content")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})

        assert "required configuration" in str(exc_info.value).lower()

    def test_plugin_manager_integration(self):
        """
        Verify plugins work with the plugin manager.
        """
        plugin_manager = PluginManager()

        # Test that migrated plugins are available
        available_plugins = plugin_manager.list_plugins()
        assert "read_file_content" in available_plugins

        # Test plugin execution through plugin manager
        with (
            patch("pathlib.Path.read_text") as mock_read,
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.is_file") as mock_is_file,
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = True
            mock_read.return_value = "test content"

            result = plugin_manager.execute_plugin(
                "read_file_content", {"file_path": "test.txt"}
            )

            assert result["content"] == "test content"
            assert result["status"] == "success"

    def test_plugin_metadata_completeness(self):
        """
        Verify plugins have complete metadata.
        """
        global_registry.load_all_plugins()

        metadata = global_registry.get_metadata("read_file_content")

        # Check required metadata fields
        assert metadata.name, "Plugin missing name"
        assert metadata.version, "Plugin missing version"
        assert metadata.description, "Plugin missing description"
        assert metadata.category, "Plugin missing category"

        # Verify metadata types
        assert isinstance(metadata.tags, list)
        assert isinstance(metadata.required_config, list)
        assert isinstance(metadata.optional_config, list)


def test_backward_compatibility():
    """
    Verify backward compatibility with existing systems.
    """
    plugin_manager = PluginManager()

    # Should be able to list plugins
    plugins = plugin_manager.list_plugins()
    assert isinstance(plugins, list)
    assert "read_file_content" in plugins

    # Should be able to execute plugin
    with (
        patch("pathlib.Path.read_text") as mock_read,
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.is_file") as mock_is_file,
    ):
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_read.return_value = "test content"

        result = plugin_manager.execute_plugin(
            "read_file_content", {"file_path": "test.txt"}
        )

        assert "content" in result
        assert "status" in result


def test_all_migrated_plugins_registered():
    """
    Verify all migrated plugins are properly registered.
    """
    global_registry.load_all_plugins()
    plugins = global_registry.list_plugins()

    expected_plugins = [
        "read_file_content",
        "write_file_content",
        "check_tcp_connection",
        "local_command",
        "ssh_command",
        "compress_file",
        "aws_secrets_manager",
        "azure_key_vault",
        "database_operations",
        "google_secret_manager",
        "hashicorp_vault",
        "run_http_request",
        "send_email",
        "uncompress_file",
    ]

    for plugin in expected_plugins:
        assert plugin in plugins, f"Plugin {plugin} not found in registry"
    assert len(plugins) >= len(expected_plugins)
