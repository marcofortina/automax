"""
Tests for cli.py CLI interface.
"""

import os
import subprocess


def test_main_help(logger):
    """
    Verify that running main with --help returns 0.
    """
    cwd = os.path.join(os.path.dirname(__file__), "../../src")
    result = subprocess.run(
        ["python3", "-m", "automax", "--help"], cwd=cwd, capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Automax - YAML-driven automation framework" in result.stdout


def test_main_list(tmp_path):
    """
    Verify --list shows available steps.
    """
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Create fake SSH key for testing
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    fake_key = ssh_dir / "id_ed25519"
    fake_key.write_text("fake-ssh-key-for-testing")

    # Create temporary config file
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
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

    result = subprocess.run(
        [
            "python3",
            "-m",
            "automax",
            "list-steps",
            "--config",
            str(config_path),
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

    # Create fake SSH key for testing
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    fake_key = ssh_dir / "id_ed25519"
    fake_key.write_text("fake-ssh-key-for-testing")

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
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

    result = subprocess.run(
        [
            "python3",
            "-m",
            "automax",
            "run",
            "--config",
            str(config_path),
            "--steps",
            "1",
            "--dry-run",
        ],
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

    # Create fake SSH key for testing
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    fake_key = ssh_dir / "id_ed25519"
    fake_key.write_text("fake-ssh-key-for-testing")

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
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

    cwd = os.path.join(os.path.dirname(__file__), "../../src")
    result = subprocess.run(
        [
            "python3",
            "-m",
            "automax",
            "run",
            "--config",
            str(config_path),
            "--steps",
            "999",
        ],
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
    cwd = os.path.join(os.path.dirname(__file__), "../../src")
    result = subprocess.run(
        [
            "python3",
            "-m",
            "automax",
            "run",
            "--config",
            str(invalid_config),
            "--steps",
            "1",
        ],
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

    # Create fake SSH key for testing
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    fake_key = ssh_dir / "id_ed25519"
    fake_key.write_text("fake-ssh-key-for-testing")

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
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

    cwd = os.path.join(os.path.dirname(__file__), "../../src")
    result = subprocess.run(
        ["python3", "-m", "automax", "validate", "--config", str(config_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "Validation successful" in combined_output
    assert "Validate-only mode" in combined_output
    assert "Executing local command" not in combined_output  # No execution
