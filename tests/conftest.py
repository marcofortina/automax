"""
Global pytest fixtures for Automax.
"""

import pytest

from automax.core.managers.config_manager import ConfigManager
from automax.core.managers.logger_manager import LoggerManager
from automax.core.managers.plugin_manager import PluginManager


@pytest.fixture
def cfg():
    """Load the real config/config.yaml for tests."""
    config_mgr = ConfigManager("examples/config/config.yaml")
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
    pm = PluginManager(logger=logger)
    pm.load_plugins()
    return pm
