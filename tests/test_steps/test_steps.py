"""
Tests for step execution in Automax using YAML configurations.
Includes tests for StepManager, SubStepManager, and ValidationManager.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.step_manager import StepManager
from automax.core.managers.substep_manager import SubStepManager
from automax.core.managers.validation_manager import ValidationManager


@pytest.fixture
def mock_yaml(tmp_path):
    """Create mock YAML files for step1 and step2 in a temporary directory."""
    step1_dir = tmp_path / "step1"
    step1_dir.mkdir()
    (step1_dir / "step1.yaml").write_text(
        """
description: "Test step 1"
substeps:
  - id: "1"
    description: "Test substep 1"
    plugin: "run_local_command"
    params:
      command: "echo test"
    output_key: "test_output"
  - id: "2"
    description: "Test substep 2"
    plugin: "run_local_command"
    params:
      command: "echo {temp_dir}"
"""
    )

    step2_dir = tmp_path / "step2"
    step2_dir.mkdir()
    (step2_dir / "step2.yaml").write_text(
        """
description: "Test step 2"
substeps:
  - id: "1"
    description: "Test substep"
    plugin: "run_local_command"
    retry: 2
    params:
      command: "echo test2"
"""
    )

    return tmp_path


def test_step1_success(cfg, logger, plugin_manager, mock_yaml):
    """Verify step1 executes successfully with dry-run using mock YAML."""
    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)
    assert step_mgr.run(step_ids=["1"], dry_run=True) is True


def test_step1_failure(cfg, logger, plugin_manager, mock_yaml, monkeypatch):
    """Simulate failure in plugin for step1."""

    def mock_utility(**kwargs):
        raise Exception("Simulated failure")

    monkeypatch.setattr(plugin_manager, "get_plugin", lambda name: mock_utility)

    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)
    with pytest.raises(AutomaxError):
        step_mgr.run(step_ids=["1"], dry_run=False)


def test_step2_success(cfg, logger, plugin_manager, mock_yaml):
    """Verify step2 executes successfully with dry-run using mock YAML."""
    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)
    assert step_mgr.run(step_ids=["2"], dry_run=True) is True


def test_substep_retry_success(cfg, logger, plugin_manager, mock_yaml):
    """Test retry logic in SubStepManager on success after failure."""
    substeps_cfg = [
        {
            "id": "1",
            "description": "Retry test",
            "plugin": "run_local_command",
            "retry": 2,
            "params": {"command": "echo retry"},
        }
    ]
    attempt = 0

    def mock_utility(**kwargs):
        nonlocal attempt
        attempt += 1
        if attempt < 2:
            raise Exception("Fail on first attempt")
        return "Success"

    with patch.object(plugin_manager, "get_plugin", return_value=mock_utility):
        sub_mgr = SubStepManager(cfg, logger, plugin_manager, "2", substeps_cfg)
        assert sub_mgr.run(dry_run=False) is True
        assert attempt == 2  # Retried once


def test_substep_context_output(cfg, logger, plugin_manager, mock_yaml):
    """Test output context propagation between sub-steps."""
    cfg["steps_dir"] = str(mock_yaml)
    step_mgr = StepManager(cfg, logger, plugin_manager)

    # Mock utility to return output
    def mock_utility1(**kwargs):
        return MagicMock(stdout=cfg["temp_dir"])

    def mock_utility2(**kwargs):
        assert kwargs["command"] == f"echo {cfg['temp_dir']}"
        return "Success"

    with patch.object(
        plugin_manager, "get_plugin", side_effect=[mock_utility1, mock_utility2]
    ):
        assert step_mgr.run(step_ids=["1"], dry_run=False) is True


def test_validation_success(cfg, logger, plugin_manager, mock_yaml):
    """Test successful validation of step YAML."""
    cfg["steps_dir"] = str(mock_yaml)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    validator.validate_step_yaml("1")  # No exception means success


def test_validation_failure_missing_param(cfg, logger, plugin_manager, tmp_path):
    """Test validation failure due to missing required param."""
    invalid_yaml = tmp_path / "step1" / "step1.yaml"
    invalid_yaml.parent.mkdir()
    invalid_yaml.write_text(
        """
description: "Invalid step"
substeps:
  - id: "1"
    description: "Invalid substep"
    plugin: "run_local_command"
    params: {}  # Missing 'command'
"""
    )
    cfg["steps_dir"] = str(tmp_path)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    with pytest.raises(AutomaxError, match="Missing required param 'command'"):
        validator.validate_step_yaml("1")


def test_validation_failure_invalid_type(cfg, logger, plugin_manager, tmp_path):
    """Test validation failure due to invalid param type."""
    invalid_yaml = tmp_path / "step1" / "step1.yaml"
    invalid_yaml.parent.mkdir()
    invalid_yaml.write_text(
        """
description: "Invalid step"
substeps:
  - id: "1"
    description: "Invalid substep"
    plugin: "run_local_command"
    params:
      command: 123  # Should be str
"""
    )
    cfg["steps_dir"] = str(tmp_path)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    with pytest.raises(AutomaxError, match="Invalid type for 'command'"):
        validator.validate_step_yaml("1")


def test_validation_failure_missing_placeholder(cfg, logger, plugin_manager, tmp_path):
    """Test validation failure due to missing placeholder key."""
    invalid_yaml = tmp_path / "step1" / "step1.yaml"
    invalid_yaml.parent.mkdir()
    invalid_yaml.write_text(
        """
description: "Invalid step"
substeps:
  - id: "1"
    description: "Invalid substep"
    plugin: "run_local_command"
    params:
      command: "ls {missing_key}"
"""
    )
    cfg["steps_dir"] = str(tmp_path)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    with pytest.raises(AutomaxError, match="Missing config key for placeholder"):
        validator.validate_step_yaml("1")


def test_cli_args_validation_success(cfg, logger, plugin_manager, mock_yaml):
    """Test successful CLI args validation."""
    cfg["steps_dir"] = str(mock_yaml)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    validator.validate_cli_args({"1": None, "2": None})  # No exception


def test_cli_args_validation_failure(cfg, logger, plugin_manager, mock_yaml):
    """Test CLI args validation failure for non-existent step."""
    cfg["steps_dir"] = str(mock_yaml)
    validator = ValidationManager(cfg, plugin_manager, Path(cfg["steps_dir"]))
    with pytest.raises(AutomaxError, match="Invalid step ID 3"):
        validator.validate_cli_args({"3": None})
