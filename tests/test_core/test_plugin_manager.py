"""
Tests for PluginManager class with the new class-based plugin system.
"""

import pytest

from automax.core.managers.plugin_manager import PluginManager
from automax.plugins.exceptions import PluginError, PluginExecutionError


@pytest.fixture(autouse=True)
def clean_plugins(logger):
    """
    Ensure a clean plugin registry before each test.
    """
    # Clear any cached plugin state
    from automax.plugins.registry import global_registry

    global_registry._plugins.clear()
    global_registry._metadata.clear()
    global_registry._loaded = False

    return PluginManager(logger)


# ---------------------------------------------------------------------------
# Plugin loading and listing tests
# ---------------------------------------------------------------------------


def test_load_plugins_success(logger, clean_plugins):
    """
    Verify that valid plugins are loaded and registered correctly.
    """
    plugin_mgr = PluginManager(logger=logger)

    # Verify plugins are available through PluginManager methods
    available_plugins = plugin_mgr.list_plugins()

    # Should have some basic plugins available
    assert len(available_plugins) > 0

    # Check that specific plugins are present
    expected_plugins = ["local_command", "ssh_command", "read_file_content"]
    for plugin_name in expected_plugins:
        assert (
            plugin_name in available_plugins
        ), f"Plugin {plugin_name} should be available"

    # Verify we can get plugin classes
    for plugin_name in expected_plugins:
        plugin_class = plugin_mgr.get_plugin(plugin_name)
        assert (
            plugin_class is not None
        ), f"Should be able to get plugin class for {plugin_name}"
        assert hasattr(
            plugin_class, "execute"
        ), f"Plugin {plugin_name} should have execute method"
        assert hasattr(
            plugin_class, "METADATA"
        ), f"Plugin {plugin_name} should have METADATA"


def test_load_plugins_duplicate(logger, clean_plugins):
    """
    Verify that plugin registry handles duplicate plugin names correctly.
    """
    plugin_mgr = PluginManager(logger=logger)

    # Get initial list of plugins
    initial_plugins = plugin_mgr.list_plugins()

    # Verify plugin manager works without throwing duplicate errors
    # The new class-based system should handle duplicates through the registry
    assert len(initial_plugins) > 0

    # All plugin names should be unique
    plugin_names = plugin_mgr.list_plugins()
    assert len(plugin_names) == len(set(plugin_names)), "Plugin names should be unique"


# ---------------------------------------------------------------------------
# get_plugin() tests
# ---------------------------------------------------------------------------


def test_get_plugin_success(logger, clean_plugins):
    """
    Verify that get_plugin() retrieves valid plugin classes.
    """
    plugin_mgr = PluginManager(logger=logger)

    # First ensure plugins are loaded by calling list_plugins
    available_plugins = plugin_mgr.list_plugins()
    assert (
        "local_command" in available_plugins
    ), "local_command plugin should be available"

    # Test getting plugin classes for known plugins
    plugin_class = plugin_mgr.get_plugin("local_command")
    assert plugin_class is not None
    assert hasattr(plugin_class, "execute")
    assert hasattr(plugin_class, "METADATA")
    assert plugin_class.METADATA.name == "local_command"


def test_get_plugin_failure(logger, clean_plugins):
    """
    Verify that get_plugin() raises appropriate error when plugin not found.
    """
    plugin_mgr = PluginManager(logger=logger)

    with pytest.raises(KeyError, match="Plugin not found: nonexistent_plugin"):
        plugin_mgr.get_plugin("nonexistent_plugin")


# ---------------------------------------------------------------------------
# execute_plugin() tests
# ---------------------------------------------------------------------------


def test_execute_plugin_success(tmp_path, logger, clean_plugins):
    """
    Verify that execute_plugin() can execute a plugin successfully.
    """
    plugin_mgr = PluginManager(logger=logger)

    # Test with read_file_content plugin
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    result = plugin_mgr.execute_plugin(
        "read_file_content", {"file_path": str(test_file)}
    )

    assert result is not None
    assert "content" in result
    assert result["content"] == "test content"


def test_execute_plugin_failure(logger, clean_plugins):
    """
    Verify that execute_plugin() raises appropriate error for invalid plugin.
    """
    plugin_mgr = PluginManager(logger=logger)

    with pytest.raises(PluginError, match="Plugin 'nonexistent_plugin' not found"):
        plugin_mgr.execute_plugin("nonexistent_plugin", {})


def test_execute_plugin_invalid_params(logger, clean_plugins):
    """
    Verify that execute_plugin() handles invalid parameters correctly.
    """
    plugin_mgr = PluginManager(logger=logger)

    # Test with missing required parameters
    with pytest.raises(PluginExecutionError):
        plugin_mgr.execute_plugin("read_file_content", {})  # Missing file_path


# ---------------------------------------------------------------------------
# Plugin availability tests
# ---------------------------------------------------------------------------


def test_list_plugins_consistency(logger, clean_plugins):
    """
    Verify that list_plugins() returns consistent results.
    """
    plugin_mgr = PluginManager(logger=logger)

    first_list = plugin_mgr.list_plugins()
    second_list = plugin_mgr.list_plugins()

    # Should return the same plugins in the same order
    assert first_list == second_list
    assert len(first_list) == len(second_list)


def test_plugin_manager_initialization(logger):
    """
    Verify that PluginManager initializes correctly with and without logger.
    """
    # Test with logger
    plugin_mgr_with_logger = PluginManager(logger=logger)
    assert plugin_mgr_with_logger.logger == logger

    # Test without logger
    plugin_mgr_without_logger = PluginManager()
    assert plugin_mgr_without_logger.logger is None

    # Both should be able to list plugins
    plugins_with_logger = plugin_mgr_with_logger.list_plugins()
    plugins_without_logger = plugin_mgr_without_logger.list_plugins()

    assert len(plugins_with_logger) > 0
    assert len(plugins_without_logger) > 0
    assert plugins_with_logger == plugins_without_logger
