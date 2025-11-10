"""
Tests for cli.py CLI interface.
"""

import os
import subprocess
from unittest.mock import patch

import pytest

from automax.cli import cli_main


def test_main_help(logger):
    """Verify that running main with --help returns 0."""
    cwd = os.path.join(os.path.dirname(__file__), "../src")
    result = subprocess.run(
        ["python3", "-m", "automax", "--help"], cwd=cwd, capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Automax - YAML-driven automation framework" in result.stdout


def test_main_list(tmp_path, cfg):
    """Verify --list shows available steps."""
    result = subprocess.run(
        [
            "python3",
            "-m",
            "automax",
            "--list",
            "--config",
            "tests/config/config.yaml",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Available steps" in result.stdout
    assert "1 2" in result.stdout  # Assuming step1 and step2 exist


def test_main_execution_success(tmp_path):
    """Integration test: Execute a valid step and verify logs/output."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Use the example SSH key
    ssh_key_path = os.path.abspath("examples/.ssh/id_ed25519")

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        f.write(
            f"""
ssh:
  private_key: "{ssh_key_path}"
  timeout: 300
log_dir: "{log_dir}"
log_level: "INFO"
json_log: false
temp_dir: "/tmp"
steps_dir: "examples/steps"
"""
        )

    result = subprocess.run(
        ["python3", "-m", "automax", "1", "--config", str(config_path), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "GLOBAL RESULT: SUCCESS" in combined_output

    # Verify log file exists and contains expected content
    log_files = list(log_dir.glob("*.log"))
    assert len(log_files) > 0
    with open(log_files[0], "r") as f:
        log_content = f.read()
        assert "[DRY-RUN]" in log_content
        assert "RESULT : OK" in log_content


def test_main_execution_failure(tmp_path):
    """Integration test: Execute with invalid step and verify failure."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Use the example SSH key
    ssh_key_path = os.path.abspath("examples/.ssh/id_ed25519")

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        f.write(
            f"""
ssh:
  private_key: "{ssh_key_path}"
  timeout: 300
log_dir: "{log_dir}"
log_level: "INFO"
json_log: false
temp_dir: "/tmp"
steps_dir: "examples/steps"
"""
        )

    cwd = os.path.join(os.path.dirname(__file__), "../src")
    result = subprocess.run(
        ["python3", "-m", "automax", "999", "--config", str(config_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    combined_output = result.stdout + result.stderr
    assert "Validation failed" in combined_output
    assert "Invalid step ID 999" in combined_output

    # Verify error log if created
    err_files = list(log_dir.glob("*.err"))
    if err_files:
        with open(err_files[0], "r") as f:
            err_content = f.read()
            assert "ERROR" in err_content


def test_main_invalid_config(tmp_path):
    """Integration test: Run with invalid config and verify failure."""
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text(":::")  # Invalid YAML to trigger YAMLError
    cwd = os.path.join(os.path.dirname(__file__), "../src")
    result = subprocess.run(
        ["python3", "-m", "automax", "1", "--config", str(invalid_config)],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    combined_output = result.stdout + result.stderr
    assert "Invalid YAML" in combined_output or "Missing required" in combined_output


def test_main_validate_only(tmp_path):
    """Integration test: Run with --validate-only and verify no execution."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Use the test SSH key
    ssh_key_path = os.path.abspath("examples/.ssh/id_ed25519")

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        f.write(
            f"""
ssh:
  private_key: "{ssh_key_path}"
  timeout: 300
log_dir: "{log_dir}"
log_level: "INFO"
json_log: false
temp_dir: "/tmp"
steps_dir: "examples/steps"
"""
        )

    cwd = os.path.join(os.path.dirname(__file__), "../src")
    result = subprocess.run(
        ["python3", "-m", "automax", "--validate-only", "--config", str(config_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "Validation successful" in combined_output
    assert "Validate-only mode" in combined_output
    assert "Executing local command" not in combined_output  # No execution


def test_main_keyboard_interrupt(monkeypatch):
    """Simulate KeyboardInterrupt during execution by testing main function directly."""
    with patch(
        "sys.argv", ["-m", "automax", "1", "--config", "examples/config/config.yaml"]
    ):
        with patch("automax.core.managers.step_manager.StepManager.run") as mock_run:
            mock_run.side_effect = KeyboardInterrupt
            with pytest.raises(SystemExit) as exc:
                cli_main()
            assert exc.value.code == 1
