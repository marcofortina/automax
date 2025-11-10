"""
Tests for PluginManager class: plugin loading, registry behavior, and get_plugin() retrieval.
"""

import sys

import pytest

from automax.core.managers.plugin_manager import PluginManager


@pytest.fixture(autouse=True)
def clean_plugins(logger):
    """
    Ensure a clean plugin registry and sys.modules cache before each test.
    Provides a fresh PluginManager instance.
    """
    # Clear Python module cache for plugins
    for mod in list(sys.modules.keys()):
        if mod.startswith("plugins."):
            sys.modules.pop(mod)
    return PluginManager(logger)


# ---------------------------------------------------------------------------
# Plugin loading tests
# ---------------------------------------------------------------------------


def test_load_plugins_success(tmp_path, logger, clean_plugins):
    """Verify that valid plugins are loaded and registered correctly."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Create dummy local plugin
    (plugins_dir / "local_command.py").write_text(
        """
def run_local_command(command, logger=None, fail_fast=True, dry_run=False):
    return 0
REGISTER_UTILITIES = [("run_local_command", run_local_command)]
SCHEMA = {'command': {'type': str, 'required': True}}
"""
    )

    # Create dummy SSH plugin
    (plugins_dir / "ssh_command.py").write_text(
        """
def run_ssh_command(host, key_path, command, logger=None, timeout=10, fail_fast=True, user=None, port=22, dry_run=False):
    return 0
REGISTER_UTILITIES = [("run_ssh_command", run_ssh_command)]
SCHEMA = {'host': {'type': str, 'required': True}}
"""
    )

    # Initialize manager with custom plugin dir
    plugin_mgr = PluginManager(logger, plugins_dir=plugins_dir)
    plugin_mgr.load_plugins()

    # Verify registry contents
    assert "run_local_command" in plugin_mgr.registry
    assert "run_ssh_command" in plugin_mgr.registry
    assert callable(plugin_mgr.registry["run_local_command"])
    assert callable(plugin_mgr.registry["run_ssh_command"])

    # Verify schemas
    assert "run_local_command" in plugin_mgr.schemas
    assert "command" in plugin_mgr.schemas["run_local_command"]


def test_load_plugins_duplicate(tmp_path, logger, clean_plugins):
    """Verify that duplicate utility names raise ValueError."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "plugin1.py").write_text(
        'REGISTER_UTILITIES = [("dup_func", lambda: None)]'
    )
    (plugins_dir / "plugin2.py").write_text(
        'REGISTER_UTILITIES = [("dup_func", lambda: None)]'
    )

    plugin_mgr = PluginManager(logger, plugins_dir=plugins_dir)
    with pytest.raises(ValueError, match="Duplicate utility name"):
        plugin_mgr.load_plugins()


def test_load_plugins_failure(tmp_path, logger, clean_plugins, caplog):
    """Verify that a broken plugin logs an error and continues loading others."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "bad_plugin.py").write_text("invalid syntax")

    plugin_mgr = PluginManager(logger, plugins_dir=plugins_dir)
    plugin_mgr.load_plugins()

    assert "Failed to load plugin" in caplog.text


# ---------------------------------------------------------------------------
# get_plugin() tests
# ---------------------------------------------------------------------------


def test_get_plugin_success(tmp_path, logger, clean_plugins):
    """Verify that get_plugin() retrieves a valid utility function."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Dummy plugin providing one utility
    plugin_file = plugins_dir / "dummy_plugin.py"
    plugin_file.write_text(
        """
def dummy_func():
    return 123
REGISTER_UTILITIES = [("dummy_func", dummy_func)]
"""
    )

    plugin_mgr = PluginManager(logger, plugins_dir=plugins_dir)
    plugin_mgr.load_plugins()
    func = plugin_mgr.get_plugin("dummy_func")

    assert callable(func)
    assert func() == 123


def test_get_plugin_failure(tmp_path, logger, clean_plugins):
    """Verify that get_plugin() raises KeyError when utility not found."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_mgr = PluginManager(logger, plugins_dir=plugins_dir)
    plugin_mgr.load_plugins()

    with pytest.raises(KeyError, match="Utility 'nonexistent' is not registered"):
        plugin_mgr.get_plugin("nonexistent")


# ---------------------------------------------------------------------------
# get_schema() tests
# ---------------------------------------------------------------------------


def test_get_schema_success(tmp_path, logger, clean_plugins):
    """Verify that get_schema() retrieves a valid schema."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Dummy plugin with SCHEMA
    plugin_file = plugins_dir / "dummy_plugin.py"
    plugin_file.write_text(
        """
def dummy_func():
    pass
REGISTER_UTILITIES = [("dummy_func", dummy_func)]
SCHEMA = {'param': {'type': str, 'required': True}}
"""
    )

    plugin_mgr = PluginManager(logger, plugins_dir=plugins_dir)
    plugin_mgr.load_plugins()
    schema = plugin_mgr.get_schema("dummy_func")

    assert isinstance(schema, dict)
    assert "param" in schema


def test_get_schema_failure(tmp_path, logger, clean_plugins):
    """Verify that get_schema() raises KeyError when no schema defined."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Dummy plugin without SCHEMA
    plugin_file = plugins_dir / "dummy_plugin.py"
    plugin_file.write_text(
        """
def dummy_func():
    pass
REGISTER_UTILITIES = [("dummy_func", dummy_func)]
"""
    )

    plugin_mgr = PluginManager(logger, plugins_dir=plugins_dir)
    plugin_mgr.load_plugins()

    with pytest.raises(KeyError, match="No SCHEMA defined for utility 'dummy_func'"):
        plugin_mgr.get_schema("dummy_func")
