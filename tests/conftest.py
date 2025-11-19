"""
Global pytest fixtures for Automax.
"""

from pathlib import Path

import pytest

from automax.core.managers.config_manager import ConfigManager
from automax.core.managers.logger_manager import LoggerManager
from automax.core.managers.plugin_manager import PluginManager


@pytest.fixture
def cfg(tmp_path):
    """
    Load a temporary config with fake SSH key for tests.
    """
    # Create fake SSH key for testing
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    fake_key = ssh_dir / "id_ed25519"
    fake_key.write_text("fake-ssh-key-for-testing")

    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Create temporary config file
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        f.write(
            f"""
ssh:
  private_key: "{fake_key}"
  timeout: 300
log_dir: "{log_dir}"
log_level: "INFO"
json_log: false
temp_dir: "/tmp"
steps_dir: "examples/steps"
"""
        )

    config_mgr = ConfigManager(Path(config_file))
    return config_mgr.cfg


@pytest.fixture
def logger(tmp_path):
    """
    Provide a LoggerManager instance for tests with json_log=False.
    """
    return LoggerManager(log_directory=tmp_path, log_level="DEBUG")


@pytest.fixture
def logger_with_json(tmp_path):
    """
    Provide a LoggerManager instance with json_log=True.
    """
    return LoggerManager(log_directory=tmp_path, log_level="DEBUG", json_log=True)


@pytest.fixture
def plugin_manager(logger):
    """
    Provide a PluginManager instance with plugins loaded.
    """
    pm = PluginManager(logger=logger)
    return pm
