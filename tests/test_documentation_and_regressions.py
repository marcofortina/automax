# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest
from click.testing import CliRunner

from automax.cli.cli import cli
from automax.core.engine import AutomaxEngine
from automax.core.models import ExecutionContext, Target
from automax.core.state import StateStore


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_documented_builtin_plugin_list_matches_registry():
    documented = set()
    in_block = False
    for line in Path("docs/plugins/index.md").read_text(encoding="utf-8").splitlines():
        if line.strip() == "```text":
            in_block = True
            continue
        if in_block and line.strip() == "```":
            break
        if in_block and line.strip():
            documented.add(line.strip())

    assert documented == set(AutomaxEngine().plugin_registry.names())


def test_documentation_does_not_reference_removed_legacy_artifacts():
    forbidden = re.compile(
        r"database_odbc_examples|aws-secrets-manager|azure-key-vault|"
        r"google-secret-manager|hashicorp-vault|compress-file|uncompress-file|"
        r"send-email|run-http-request|check-icmp|check-tcp|"
        r"read-file-content|write-file-content|database_operations|"
        r"local_command|ssh_command|pyodbc|boto3|hvac|ping3"
    )
    searched = [Path("README.md"), Path("requirements.txt"), *Path("docs").rglob("*.md")]
    offenders = []
    for path in searched:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if forbidden.search(line):
                offenders.append(f"{path}:{number}:{line}")

    assert offenders == []


def test_reference_links_in_markdown_exist():
    markdown_files = [Path("README.md"), *Path("docs").rglob("*.md")]
    missing = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
    for path in markdown_files:
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                missing.append(f"{path} -> {target}")

    assert missing == []


def test_all_example_jobs_validate(tmp_path: Path, monkeypatch):
    key_path_file = write(tmp_path / "ssh-key-path.txt", str(tmp_path / "id_ed25519"))
    write(tmp_path / "id_ed25519", "dummy-key")
    monkeypatch.setenv("AUTOMAX_SSH_USER", "automax")

    inventory_by_job = {
        "database-sqlite.yaml": "examples/next/inventory/local.yaml",
        "local-smoke.yaml": "examples/next/inventory/local.yaml",
        "template-workflow.yaml": "examples/next/inventory/local.yaml",
    }
    for job_path in sorted(Path("examples/next/jobs").glob("*.yaml")):
        inventory = inventory_by_job.get(job_path.name, "examples/next/inventory/lab.yaml")
        secrets = None
        vars_path = None
        if inventory.endswith("lab.yaml"):
            secrets = write(
                tmp_path / f"{job_path.stem}-secrets.yaml",
                f"""
secrets:
  ssh_user:
    provider: env
    name: AUTOMAX_SSH_USER
  ssh_key_file:
    provider: file
    path: {key_path_file}
""",
            )
            vars_path = "examples/next/vars/lab.yaml"
        AutomaxEngine().validate(
            job_path=str(job_path),
            inventory_path=inventory,
            vars_path=vars_path,
            secrets_path=str(secrets) if secrets else None,
        )


def test_substep_targets_are_respected_in_plan(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: substep-targets
strategy:
  mode: serial
tasks:
  - id: route
    targets: all
    steps:
      - id: split
        substeps:
          - id: only_one
            targets: server:one
            use: local.command
            with:
              command: "true"
          - id: only_two
            targets: server:two
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  one:
    host: 127.0.0.1
  two:
    host: 127.0.0.1
""",
    )

    result = CliRunner().invoke(cli, ["plan", "--job", str(job), "--inventory", str(inventory)])

    assert result.exit_code == 0, result.output
    assert "one task.route:step.split:substep.only_one" in result.output
    assert "two task.route:step.split:substep.only_two" in result.output
    assert "one task.route:step.split:substep.only_two" not in result.output
    assert "two task.route:step.split:substep.only_one" not in result.output


def test_run_from_task_skips_previous_task(tmp_path: Path):
    first_marker = tmp_path / "first"
    second_marker = tmp_path / "second"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: restart-from-task
tasks:
  - id: first
    targets: all
    steps:
      - id: local
        substeps:
          - id: write_first
            use: local.command
            with:
              command: "printf first > {first_marker}"
  - id: second
    targets: all
    steps:
      - id: local
        substeps:
          - id: write_second
            use: local.command
            with:
              command: "printf second > {second_marker}"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--state-dir",
            str(tmp_path / "runs"),
            "--from",
            "task.second",
        ],
    )

    assert result.exit_code == 0, result.output
    assert not first_marker.exists()
    assert second_marker.read_text(encoding="utf-8") == "second"


def test_sqlite_commit_false_rolls_back(tmp_path: Path):
    plugin = AutomaxEngine().plugin_registry.get("db.sqlite.query")
    context = ExecutionContext(
        run_id="test-run",
        dry_run=False,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="controller", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )
    database = tmp_path / "rollback.sqlite"

    result = plugin.execute(
        {
            "connection": {"path": str(database)},
            "statements": [
                "CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT NOT NULL)",
                "INSERT INTO demo(name) VALUES ('rolled-back')",
            ],
            "output": "none",
            "commit": False,
        },
        context,
    )
    assert result.ok, result.stderr

    select = plugin.execute(
        {
            "connection": {"path": str(database)},
            "query": "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'demo'",
            "output": "scalar",
            "fetch": "one",
        },
        context,
    )

    assert select.ok, select.stderr
    assert select.data["scalar"] is None


def test_target_variables_override_cli_and_job_vars(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: variable-precedence
vars:
  owner: job-owner
tasks:
  - id: vars
    targets: all
    steps:
      - id: local
        substeps:
          - id: echo
            use: local.command
            with:
              command: "printf '{{ vars.owner }}'"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  controller:
    host: 127.0.0.1
    vars:
      owner: target-owner
""",
    )

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--state-dir",
            str(tmp_path / "runs"),
            "--var",
            "owner=cli-owner",
        ],
    )

    assert result.exit_code == 0, result.output
    run_id = [line.split(":", 1)[1].strip() for line in result.output.splitlines() if line.startswith("Run ID:")][0]
    store = StateStore(tmp_path / "runs", run_id)
    with store.connect() as conn:
        row = conn.execute(
            """
            SELECT output_json
              FROM nodes
             WHERE run_id = ? AND node_id = ? AND target = ?
            """,
            (run_id, "task.vars:step.local:substep.echo", "controller"),
        ).fetchone()
    assert row is not None
    output = json.loads(row["output_json"])
    assert output["stdout"] == "target-owner"


def test_failure_policy_stop_task_skips_later_steps_in_same_task(tmp_path: Path):
    skipped_marker = tmp_path / "skipped"
    next_task_marker = tmp_path / "next-task"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: stop-task-policy
failurePolicy:
  onFailure: stop_task
tasks:
  - id: failing_task
    targets: all
    steps:
      - id: fail
        substeps:
          - id: bad
            use: local.command
            with:
              command: "false"
      - id: must_skip
        substeps:
          - id: write_skipped
            use: local.command
            with:
              command: "printf bad > {skipped_marker}"
  - id: next_task
    targets: all
    steps:
      - id: run
        substeps:
          - id: write_next
            use: local.command
            with:
              command: "printf ok > {next_task_marker}"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 1, result.output
    assert not skipped_marker.exists()
    assert next_task_marker.read_text(encoding="utf-8") == "ok"


def test_ssh_boolean_options_are_parsed_strictly():
    from automax.core.ssh import SshError, SshSessionManager

    assert SshSessionManager._coerce_bool("false", True) is False
    assert SshSessionManager._coerce_bool("true", False) is True
    assert SshSessionManager._coerce_bool(None, False) is False
    with pytest.raises(SshError):
        SshSessionManager._coerce_bool("maybe", False)


def test_secret_values_are_masked_in_persisted_result_mapping():
    from automax.core.engine import AutomaxEngine
    from automax.core.models import PluginResult

    engine = AutomaxEngine()
    result = PluginResult.success(
        stdout="token=s3cr3t-value",
        stderr="bad s3cr3t-value",
        message="message s3cr3t-value",
        data={"nested": ["s3cr3t-value"]},
    )

    mapped = engine._result_to_mapping(result, secrets={"token": "s3cr3t-value"})

    assert mapped["stdout"] == "token=***"
    assert mapped["stderr"] == "bad ***"
    assert mapped["message"] == "message ***"
    assert mapped["data"] == {"nested": ["***"]}


def test_plugins_describe_outputs_parameter_metadata():
    runner = CliRunner()
    result = runner.invoke(cli, ["plugins", "describe", "fs.template"])

    assert result.exit_code == 0, result.output
    assert "Name: fs.template" in result.output
    assert "src" in result.output
    assert "dest" in result.output
    assert "Remote session: true" in result.output
