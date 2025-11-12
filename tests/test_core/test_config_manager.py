"""
Tests for common.managers.config_manager.ConfigManager.
"""

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.config_manager import ConfigManager


def test_load_config_valid(tmp_path):
    """
    Verify loading of a valid config using ConfigManager.
    """
    key_path = tmp_path / "dummy_key"
    key_path.write_text("DUMMY_KEY")
    key_path.chmod(0o600)

    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    cfg_dict = {
        "ssh": {"private_key": str(key_path), "timeout": 300},
        "log_dir": str(log_dir),
        "steps_dir": "steps",
    }

    cfg_manager = ConfigManager()
    cfg_manager.load(cfg_dict)
    cfg = cfg_manager.cfg
    assert cfg is not None
    assert "ssh" in cfg
    assert "steps_dir" in cfg


def test_load_config_invalid_yaml(tmp_path):
    """
    Verify invalid YAML raises AutomaxError.
    """
    bad_cfg = tmp_path / "bad_config.yaml"
    bad_cfg.write_text(":::")

    cfg_manager = ConfigManager()
    with pytest.raises(AutomaxError):
        cfg_manager.load(str(bad_cfg))


def test_load_config_missing_fields(tmp_path):
    """
    Verify missing required fields raise AutomaxError.
    """
    incomplete_cfg = tmp_path / "incomplete.yaml"
    incomplete_cfg.write_text("ssh: {}")

    cfg_manager = ConfigManager()
    with pytest.raises(AutomaxError):
        cfg_manager.load(str(incomplete_cfg))


def test_load_config_invalid_paths(tmp_path):
    """
    Verify invalid paths in config raise AutomaxError.
    """
    invalid_cfg = tmp_path / "invalid.yaml"
    invalid_cfg.write_text(
        """
ssh:
  private_key: /non/existent/key
  timeout: 300
log_dir: /non/writable/dir
steps_dir: /invalid/dir
"""
    )
    cfg_manager = ConfigManager()
    with pytest.raises(AutomaxError):
        cfg_manager.load(str(invalid_cfg))
