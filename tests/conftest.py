"""
Global pytest fixtures for Automax.
"""

import os
from pathlib import Path

import pytest

from automax.core.managers.config_manager import ConfigManager
from automax.core.managers.logger_manager import LoggerManager
from automax.core.managers.plugin_manager import PluginManager


@pytest.fixture
def cfg():
    """Load the config/config.yaml for tests."""
    config_file = Path(os.path.join(os.path.dirname(__file__), "config/config.yaml"))
    config_mgr = ConfigManager(config_file)
    return config_mgr.cfg


@pytest.fixture
def logger(tmp_path):
    """Provide a LoggerManager instance for tests with json_log=False."""
    return LoggerManager(log_directory=tmp_path, log_level="DEBUG")


@pytest.fixture
def logger_with_json(tmp_path):
    """Provide a LoggerManager instance with json_log=True."""
    return LoggerManager(log_directory=tmp_path, log_level="DEBUG", json_log=True)


@pytest.fixture
def plugin_manager(logger):
    """Provide a PluginManager instance with plugins loaded."""
    plugins_path = Path(
        os.path.join(os.path.dirname(__file__), "../src/automax/plugins")
    )
    pm = PluginManager(logger=logger, plugins_dir=plugins_path)
    pm.load_plugins()
    return pm
