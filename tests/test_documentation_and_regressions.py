# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml
from click.testing import CliRunner

from automax.cli.cli import cli
from automax.core.engine import AutomaxEngine
from automax.core.models import ExecutionContext, Target
from automax.core.state import StateStore


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path



def test_python_m_cli_entrypoint_does_not_emit_runpy_warning():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path("src").resolve())
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::RuntimeWarning",
            "-m",
            "automax.cli.cli",
            "--help",
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "RuntimeWarning" not in result.stderr


def test_cli_package_exports_cli_main_lazily():
    from automax.cli import cli_main

    assert callable(cli_main)

def test_plugin_metadata_sample_formatter_is_python39_safe():
    from automax.plugins.metadata import _format_sample_value

    assert _format_sample_value("timeout", 3, indent="  ") == ["  timeout: 3"]
    assert _format_sample_value("interval", 1.5, indent="  ") == ["  interval: 1.5"]

def test_documented_builtin_plugin_list_matches_registry():
    documented = []
    in_block = False
    for line in Path("docs/plugins/index.md").read_text(encoding="utf-8").splitlines():
        if line.strip() == "```text":
            in_block = True
            continue
        if in_block and line.strip() == "```":
            break
        if in_block and line.strip():
            documented.append(line.strip())

    duplicate_names = sorted({name for name in documented if documented.count(name) > 1})
    assert duplicate_names == []
    assert set(documented) == set(AutomaxEngine().plugin_registry.names())


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




def test_plugins_audit_command_reports_builtin_readiness():
    result = CliRunner().invoke(cli, ["plugins", "audit"])

    assert result.exit_code == 0, result.output
    assert "Plugin audit:" in result.output
    assert "Result: OK" in result.output

    json_result = CliRunner().invoke(cli, ["plugins", "audit", "--format", "json"])
    assert json_result.exit_code == 0, json_result.output
    payload = json.loads(json_result.output)
    assert payload["ok"] is True
    assert payload["failure_count"] == 0
    assert payload["checked"] > 100

    docs = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in ["README.md", "docs/reference/cli.md", "docs/concepts/plugin-system.md", "docs/guides/creating-plugins.md"]
    )
    assert "automax plugins audit" in docs

def test_plugins_describe_outputs_parameter_metadata():
    runner = CliRunner()
    result = runner.invoke(cli, ["plugins", "describe", "fs.file.template"])

    assert result.exit_code == 0, result.output
    assert "Name: fs.file.template" in result.output
    assert "src" in result.output
    assert "dest" in result.output
    assert "Remote session: true" in result.output


def test_documentation_dependency_files_match_mkdocs_configuration():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    requirements = Path("requirements-docs.txt").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    required_packages = [
        "mkdocs",
        "mkdocs-material",
        "mkdocstrings",
        "mkdocstrings-python",
        "pymdown-extensions",
    ]
    for package in required_packages:
        assert package in pyproject
        assert package in requirements

    assert "theme:" in mkdocs
    assert "name: material" in mkdocs
    assert "pymdownx.superfences" in mkdocs
    assert "mkdocstrings" in mkdocs


def test_documentation_publish_workflow_and_nav_are_present():
    workflow = Path(".github/workflows/docs.yml").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert "actions/deploy-pages" in workflow
    assert "mkdocs build --strict" in workflow
    assert "site_url: https://marcofortina.github.io/automax/" in mkdocs
    assert "guides/publishing-docs.md" in mkdocs


def test_generated_plugin_reference_is_in_sync(tmp_path: Path):
    result = CliRunner().invoke(
        cli,
        ["docs", "generate-plugins", "--output", str(tmp_path / "generated.md")],
    )

    assert result.exit_code == 0, result.output
    expected = Path("docs/plugins/generated.md").read_text(encoding="utf-8")
    actual = (tmp_path / "generated.md").read_text(encoding="utf-8")
    assert actual == expected
    assert "### `fs.file.template`" in actual
    assert "| `src` | yes | `path`" in actual


def test_artifacts_reference_is_documented_in_nav():
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    docs = Path("docs/reference/artifacts.md").read_text(encoding="utf-8")

    assert "reference/artifacts.md" in mkdocs
    assert "automax artifacts list <run-id>" in docs



def test_publishable_pages_include_operator_manuals():
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    required_pages = [
        "quickstart.md",
        "concepts/architecture.md",
        "concepts/execution-model.md",
        "concepts/plugin-system.md",
        "guides/installation.md",
        "guides/first-local-job.md",
        "guides/first-ssh-job.md",
        "guides/writing-jobs.md",
        "reference/cli.md",
        "reference/security.md",
        "reference/testing-and-ci.md",
        "plugins/generated.md",
    ]
    for page in required_pages:
        assert page in mkdocs
        assert Path("docs", page).exists()


def test_documentation_home_is_a_landing_page_not_readme_clone():
    home = Path("docs/index.md").read_text(encoding="utf-8")

    assert "## Why Automax" in home
    assert "## Start here" in home
    assert "## What the public documentation covers" in home
    assert "[Quickstart](quickstart.md)" in home
    assert "[Builtin plugins](plugins/index.md)" in home


def test_job_inspection_and_recovery_workflow_is_documented():
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    cli_ref = Path("docs/reference/cli.md").read_text(encoding="utf-8")
    guide = Path("docs/guides/job-inspection-and-recovery.md").read_text(
        encoding="utf-8"
    )

    assert "guides/job-inspection-and-recovery.md" in mkdocs
    for snippet in [
        "automax inventory show",
        "automax secrets check",
        "automax plan --check",
        "automax plan --diff",
        "automax commands render",
        "automax resume --from",
    ]:
        assert snippet in guide
    assert "automax commands render" in readme
    assert "automax commands render" in cli_ref
    assert "automax run --check" in cli_ref

def test_python39_compatibility_guard_passes_on_repository(capsys):
    import runpy
    import sys

    saved_argv = sys.argv
    sys.argv = ["scripts/check-python39-compat.py"]
    try:
        try:
            runpy.run_path("scripts/check-python39-compat.py", run_name="__main__")
        except SystemExit as exc:
            assert exc.code == 0
    finally:
        sys.argv = saved_argv
    captured = capsys.readouterr()
    assert "Python 3.9 compatibility check passed" in captured.out

def test_development_tooling_uses_ruff_and_pre_commit():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    pre_commit = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert '"ruff>=0.8,<1.0"' in pyproject
    assert '"pre-commit>=4.0,<5.0"' in pyproject
    assert "black>=" not in pyproject
    assert "flake8>=" not in pyproject
    assert "isort>=" not in pyproject
    assert "astral-sh/ruff-pre-commit" in pre_commit


def test_dynamic_inventory_and_command_secrets_are_documented():
    docs = [
        Path("docs/guides/dynamic-inventory.md"),
        Path("docs/guides/command-secrets.md"),
        Path("docs/reference/inventory-vars-secrets.md"),
        Path("docs/reference/security.md"),
    ]
    missing = [path for path in docs if not path.is_file()]
    assert missing == []
    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    assert "provider: command" in combined
    assert "provider: http" in combined
    assert "shell: true" in combined
    assert "command secrets run on the controller" in combined.lower()


def test_dynamic_inventory_removed_from_future_work():
    future_work = Path("docs/reference/future-work.md").read_text(encoding="utf-8")
    assert "Dynamic inventory providers" not in future_work
    assert "inventory.command" not in future_work
    assert "secret providers" in future_work.lower()


def test_codeql_workflow_uses_node24_action_generation():
    workflow = Path(".github/workflows/codeql.yml").read_text(encoding="utf-8")
    assert "github/codeql-action/init@v4" in workflow
    assert "github/codeql-action/analyze@v4" in workflow
    assert "security-events: write" in workflow
    assert "security-extended,security-and-quality" in workflow

def test_runbook_helpers_keep_sudo_password_env_explicit():
    readme = Path("examples/runbooks/README.md").read_text(encoding="utf-8")
    assert "export AUTOMAX_SUDO_PASSWORD='...'" in readme
    assert "without installing NOPASSWD sudoers rules" in readme

    for script_path in [
        Path("examples/runbooks/scripts/run-all-checks.sh"),
        Path("examples/runbooks/scripts/run-one-check.sh"),
    ]:
        script = script_path.read_text(encoding="utf-8")
        assert 'SUDO_PASSWORD_ENV="${AUTOMAX_SUDO_PASSWORD_ENV:-AUTOMAX_SUDO_PASSWORD}"' in script
        assert '[[ -z "${!SUDO_PASSWORD_ENV:-}" ]]' in script
        assert '--sudo-password-env "$SUDO_PASSWORD_ENV"' in script



def test_run_all_checks_supports_optional_keep_going_summary():
    script = Path("examples/runbooks/scripts/run-all-checks.sh").read_text(encoding="utf-8")

    assert "--keep-going" in script
    assert "KEEP_GOING=0" in script
    assert "failed_runbooks=()" in script
    assert "== run-all summary ==" in script
    assert 'exit "$rc"' in script
    assert "failed runbooks:" in script

    readme = Path("examples/runbooks/README.md").read_text(encoding="utf-8")
    assert '"$RB/scripts/run-all-checks.sh" --keep-going' in readme

def test_plugin_smoke_runbooks_keep_file_modes_as_strings():
    offenders = []
    for runbook_path in sorted(Path("examples/runbooks/runbooks").glob("*.check.yaml")):
        data = yaml.safe_load(runbook_path.read_text(encoding="utf-8"))
        for task in data.get("tasks", []):
            for step in task.get("steps", []):
                for substep in step.get("substeps", []):
                    params = substep.get("with") or {}
                    if "mode" in params and not isinstance(params["mode"], str):
                        offenders.append(
                            f"{runbook_path}:{substep.get('id')}:{substep.get('use')}: "
                            f"mode must be quoted string, got {type(params['mode']).__name__}"
                        )

    assert offenders == []


def test_plugin_smoke_runbooks_match_archive_decompress_parameters():
    runbook_path = Path("examples/runbooks/runbooks/03-archive.check.yaml")
    data = yaml.safe_load(runbook_path.read_text(encoding="utf-8"))
    offenders = []
    for task in data.get("tasks", []):
        for step in task.get("steps", []):
            for substep in step.get("substeps", []):
                if substep.get("use") != "archive.decompress":
                    continue
                params = substep.get("with") or {}
                if "source" in params:
                    offenders.append(
                        f"{runbook_path}:{substep.get('id')}: "
                        "source is not valid for archive.decompress"
                    )

    assert offenders == []


def test_plugin_smoke_runbooks_match_auditd_search_user_schema():
    from automax.plugins.registry import build_builtin_registry

    plugin = build_builtin_registry().get("security.audit.search")
    plugin.validate({"key": "automax", "user": "deploy", "start": "recent", "end": "now"})

    runbook = yaml.safe_load(Path("examples/runbooks/runbooks/05-auditd.check.yaml").read_text(encoding="utf-8"))
    search_substeps = [
        substep
        for task in runbook.get("tasks", [])
        for step in task.get("steps", [])
        for substep in step.get("substeps", [])
        if substep.get("use") == "security.audit.search"
    ]
    assert search_substeps
    assert all(isinstance((substep.get("with") or {}).get("user"), str) for substep in search_substeps)


def test_plugin_smoke_runbooks_use_valid_node_ids():
    node_id_pattern = re.compile(r"^[A-Za-z0-9_.-]+$")
    offenders = []
    for runbook_path in sorted(Path("examples/runbooks/runbooks").glob("*.check.yaml")):
        data = yaml.safe_load(runbook_path.read_text(encoding="utf-8"))
        for task in data.get("tasks", []):
            task_id = task.get("id")
            if not isinstance(task_id, str) or not node_id_pattern.match(task_id):
                offenders.append(f"{runbook_path}: task id: {task_id!r}")
            for step in task.get("steps", []):
                step_id = step.get("id")
                if not isinstance(step_id, str) or not node_id_pattern.match(step_id):
                    offenders.append(f"{runbook_path}: step id: {step_id!r}")
                for substep in step.get("substeps", []):
                    substep_id = substep.get("id")
                    if not isinstance(substep_id, str) or not node_id_pattern.match(substep_id):
                        offenders.append(f"{runbook_path}: substep id: {substep_id!r}")

    assert offenders == []


def test_plugin_smoke_runbooks_validate_against_builtin_schemas():
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    failures = []
    for runbook_path in sorted(Path("examples/runbooks/runbooks").glob("*.check.yaml")):
        data = yaml.safe_load(runbook_path.read_text(encoding="utf-8"))
        for task in data.get("tasks", []):
            for step in task.get("steps", []):
                for substep in step.get("substeps", []):
                    plugin_name = substep.get("use")
                    params = substep.get("with") or {}
                    try:
                        registry.get(plugin_name).validate(params)
                    except Exception as exc:  # pragma: no cover - assertion reports all offenders
                        failures.append(f"{runbook_path}:{substep.get('id')}:{plugin_name}: {exc}")

    assert failures == []


def test_plugin_specific_user_and_boolean_value_schemas_do_not_use_global_fallbacks():
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    registry.get("system.cron.entry.list").validate({"user": "deploy", "sudo": True})
    registry.get("security.selinux.boolean").validate({"name": "httpd_can_network_connect", "value": True, "persist": True})










def test_rendered_file_install_mixin_covers_managed_file_plugins():
    from automax.plugins.base import RenderedFileInstallMixin
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    expected = {
        "security.audit.rule",
        "os.time.chrony.servers.set",
        "os.limits.dropin",
        "network.dns.config",
        "security.password.policy",
        "security.ssh.config",
        "security.sshd.config",
        "security.sudo.rule",
        "system.kernel.sysctl.dropin",
        "system.systemd.sysusers",
        "system.systemd.timer",
        "system.systemd.tmpfiles",
        "system.systemd.unit",
        "udev.rule",
    }
    for name in expected:
        assert isinstance(registry.get(name), RenderedFileInstallMixin)

    sudo_commands = registry.get("security.sudo.rule").manual_commands(
        {"name": "ops", "subject": "%ops", "commands": ["/usr/bin/systemctl"]},
        ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={}),
    )
    rendered = "\n".join(sudo_commands)
    assert "mktemp" in rendered
    assert "trap 'rm -f" in rendered
    assert "visudo -cf" in rendered
    assert "install -D -m 0440" in rendered

def test_read_only_command_plugin_is_shared_base_class():
    from automax.plugins.base import ReadOnlyCommandPlugin
    from automax.plugins.ops_completeness import __dict__ as ops_symbols
    from automax.plugins.registry import build_builtin_registry

    assert "_ReadOnlyCommandPlugin" not in ops_symbols

    registry = build_builtin_registry()
    expected = {
        "security.apparmor.profile_check",
        "security.audit.status",
        "security.audit.search",
        "system.cron.entry.list",
        "security.sudo.validate",
        "system.kernel.sysctl.check",
        "udev.validate",
    }
    for name in expected:
        assert isinstance(registry.get(name), ReadOnlyCommandPlugin)

    readonly_plugins = [
        name for name in registry.names() if isinstance(registry.get(name), ReadOnlyCommandPlugin)
    ]
    assert len(readonly_plugins) >= 37








def test_security_namespace_replaces_legacy_security_plugin_names():
    from automax.plugins.registry import build_builtin_registry

    old_names = [
        "apparmor.complain",
        "apparmor.disable",
        "apparmor.enforce",
        "apparmor.parser_validate",
        "apparmor.profile",
        "apparmor.profile_assert",
        "apparmor.reload",
        "apparmor.status",
        "auditd.backlog_assert",
        "auditd.reload",
        "auditd.rule",
        "auditd.rules_facts",
        "auditd.search",
        "auditd.status",
        "auditd.syscall",
        "auditd.watch",
        "authselect.profile",
        "pam.access",
        "pam.authselect",
        "pam.backup",
        "pam.faillock",
        "pam.include_assert",
        "pam.limits",
        "pam.module_assert",
        "pam.order_assert",
        "pam.pwhistory",
        "pam.restore",
        "pam.service_line",
        "pam.stack_facts",
        "pam.succeed_if",
        "pam.validate",
        "password.policy",
        "selinux.boolean",
        "selinux.context",
        "selinux.fcontext",
        "selinux.mode",
        "selinux.port",
        "selinux.restorecon",
        "sudo.assert",
        "sudo.can_run",
        "sudo.list",
        "sudo.rule",
        "sudo.validate",
        "sudoers.dropin",
        "ssh.authorized_key",
        "ssh.authorized_key_absent",
        "ssh.config",
        "ssh.fingerprint",
        "ssh.host_keygen",
        "ssh.keygen",
        "ssh.known_hosts",
        "ssh.public_key",
        "sshd.config",
        "sshd.validate",
        "secret.redact_assert",
        "secret.scan_output",
        "secret.scan_preview",
        "cert.expiry_report",
        "cert.fingerprint",
        "cert.generate_csr",
        "cert.install_ca_bundle",
        "cert.install_keypair",
        "cert.issuer_assert",
        "cert.matches_key",
        "cert.san_assert",
        "cert.self_signed",
        "cert.subject_assert",
        "cert.verify_chain",
        "pki.ca_install",
        "pki.cert_expiry_assert",
        "pki.key_permissions",
    ]
    names = set(build_builtin_registry().names())
    assert not (names & set(old_names))
    assert {
        "security.apparmor.profile_check",
        "security.audit.rules.facts",
        "security.authselect.profile",
        "security.authselect.check",
        "security.pam.stack.facts",
        "security.password.policy",
        "security.pki.cert.expiry_check",
        "security.pki.trust.install_ca",
        "security.secret.redact_check",
        "security.selinux.mode",
        "security.ssh.authorized_key.add",
        "security.ssh.authorized_key.remove",
        "security.sshd.validate",
        "security.sudo.dropin",
    } <= names

    searched = [
        Path("docs/plugins/index.md"),
        Path("docs/plugins/linux-operations.md"),
        Path("docs/plugins/generated.md"),
        Path("docs/plugins/security.md"),
        Path("docs/guides/account-access.md"),
        Path("docs/guides/linux-security-modules.md"),
        Path("examples/runbooks/RUNBOOK_INDEX.md"),
        *Path("examples/runbooks/runbooks").glob("*.check.yaml"),
    ]
    offenders = []
    for path in searched:
        text = path.read_text(encoding="utf-8")
        for old_name in old_names:
            pattern = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_name) + r"(?![A-Za-z0-9_.])")
            if pattern.search(text):
                offenders.append(f"{path}:{old_name}")
    assert offenders == []



def test_identity_namespace_replaces_legacy_user_group_plugin_names():
    from automax.plugins.registry import build_builtin_registry

    old_names = [
        "user.create",
        "user.exists",
        "user.facts",
        "user.groups_assert",
        "user.home_assert",
        "user.lock",
        "user.modify",
        "user.remove",
        "user.set_password",
        "user.shell_assert",
        "user.unlock",
        "group.create",
        "group.exists",
        "group.member_absent",
        "group.members",
        "group.remove",
    ]
    names = set(build_builtin_registry().names())
    assert not (names & set(old_names))
    assert {
        "identity.user.create",
        "identity.user.exists",
        "identity.user.facts",
        "identity.user.groups_check",
        "identity.user.home_check",
        "identity.user.lock",
        "identity.user.modify",
        "identity.user.remove",
        "identity.user.set_password",
        "identity.user.shell_check",
        "identity.user.unlock",
        "identity.group.create",
        "identity.group.exists",
        "identity.group.member.remove",
        "identity.group.members",
        "identity.group.remove",
    } <= names

    searched = [
        Path("docs/plugins/index.md"),
        Path("docs/plugins/linux-operations.md"),
        Path("docs/plugins/generated.md"),
        Path("docs/plugins/users-groups-processes.md"),
        Path("docs/guides/account-access.md"),
        Path("examples/runbooks/RUNBOOK_INDEX.md"),
        *Path("examples/runbooks/runbooks").glob("*.check.yaml"),
    ]
    offenders = []
    for path in searched:
        text = path.read_text(encoding="utf-8")
        for old_name in old_names:
            pattern = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_name) + r"(?![A-Za-z0-9_.])")
            if pattern.search(text):
                offenders.append(f"{path}:{old_name}")
    assert offenders == []

def test_storage_namespace_replaces_legacy_storage_plugin_names():
    from automax.plugins.registry import build_builtin_registry

    old_names = [
        "assert.disk",
        "blkid.assert",
        "block.empty_assert",
        "block.facts",
        "block.fs_assert",
        "block.identity",
        "block.mkfs",
        "block.mountpoint_assert",
        "block.not_mounted_assert",
        "block.partition",
        "block.partition_rescan",
        "block.rescan",
        "block.size_assert",
        "block.wipe_signatures",
        "findmnt.assert",
        "fs.bind_mount",
        "fs.disk_usage_assert",
        "fs.inode_usage_assert",
        "fs.quota",
        "fs.resize",
        "fstab.absent",
        "fstab.assert",
        "fstab.entry",
        "fstab.validate",
        "lvm.facts",
        "lvm.lv_assert",
        "lvm.lv_extend",
        "lvm.lv_present",
        "lvm.lv_remove",
        "lvm.pv_present",
        "lvm.pv_remove",
        "lvm.resizefs",
        "lvm.snapshot",
        "lvm.thin_pool",
        "lvm.vg_present",
        "lvm.vg_remove",
        "mount.absent",
        "mount.assert",
        "mount.facts",
        "mount.options_assert",
        "mount.present",
        "mount.remount",
        "multipath.flush",
        "multipath.reload",
        "multipath.status",
        "swap.absent",
        "swap.present",
        "swap.status",
    ]
    names = set(build_builtin_registry().names())
    assert not (names & set(old_names))
    assert {
        "storage.block.facts",
        "storage.block.partition.apply",
        "storage.fs.check",
        "storage.fs.facts",
        "storage.fs.resize",
        "storage.mount.check",
        "storage.mount.bind",
        "storage.fstab.add",
        "storage.swap.check",
        "storage.lvm.pv.scan",
        "storage.lvm.vg.scan",
        "storage.lvm.lv.scan",
        "storage.multipath.add",
        "storage.multipath.remove",
        "storage.quota.get",
        "storage.quota.check",
        "storage.quota.facts",
        "storage.usage.disk_check",
        "storage.usage.inode_check",
    } <= names

    searched = [
        Path("docs/plugins/index.md"),
        Path("docs/plugins/linux-operations.md"),
        Path("docs/plugins/generated.md"),
        Path("docs/plugins/kernel-storage.md"),
        Path("docs/plugins/filesystem.md"),
        Path("examples/runbooks/RUNBOOK_INDEX.md"),
        *Path("examples/runbooks/runbooks").glob("*.check.yaml"),
    ]
    offenders = []
    for path in searched:
        text = path.read_text(encoding="utf-8")
        for old_name in old_names:
            pattern = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_name) + r"(?![A-Za-z0-9_.])")
            if pattern.search(text):
                offenders.append(f"{path}:{old_name}")
    assert offenders == []



def test_os_namespace_replaces_legacy_operating_system_plugin_names():
    from automax.plugins.registry import build_builtin_registry

    old_names = [
        "alternatives.get",
        "alternatives.list",
        "alternatives.set",
        "capability.assert",
        "chrony.servers",
        "chrony.sources_assert",
        "chrony.tracking_assert",
        "env.set",
        "facts.os",
        "facts.packages",
        "hostname.set",
        "hosts.entry",
        "limits.dropin",
        "login.defs",
        "pkg.clean",
        "pkg.files",
        "pkg.hold",
        "pkg.install",
        "pkg.key.add",
        "pkg.key.remove",
        "pkg.owner",
        "pkg.query",
        "pkg.remove",
        "pkg.repo.add",
        "pkg.repo.remove",
        "pkg.repo_priority",
        "pkg.unhold",
        "pkg.update_cache",
        "pkg.upgrade",
        "pkg.verify",
        "pkg.version_assert",
        "pkg.version_pin",
        "platform.facts",
        "timedatectl.ntp",
        "timedatectl.status",
        "timedatectl.timezone",
        "tool.exists",
        "tool.version_assert",
    ]
    names = set(build_builtin_registry().names())
    assert not (names & set(old_names))
    assert {
        "os.alternatives.check",
        "os.alternatives.get",
        "os.alternatives.list",
        "os.alternatives.set",
        "os.arch.check",
        "os.capability.check",
        "os.env.check",
        "os.env.facts",
        "os.env.get",
        "os.env.remove",
        "os.env.set",
        "os.facts",
        "os.hostname.check",
        "os.hostname.get",
        "os.hostname.set",
        "os.hosts.entry.add",
        "os.hosts.entry.check",
        "os.hosts.entry.remove",
        "os.hosts.facts",
        "os.limits.dropin",
        "os.login.defs.check",
        "os.login.defs.get",
        "os.login.defs.set",
        "os.package.check",
        "os.package.facts",
        "os.package.hold.add",
        "os.package.hold.check",
        "os.package.hold.list",
        "os.package.hold.remove",
        "os.package.key.check",
        "os.package.key.list",
        "os.package.repo.check",
        "os.package.repo.list",
        "os.package.repo.priority.check",
        "os.package.repo.priority.set",
        "os.package.version.check",
        "os.package.version.pin",
        "os.platform.facts",
        "os.time.chrony.servers.check",
        "os.time.chrony.servers.get",
        "os.time.chrony.servers.set",
        "os.time.ntp.check",
        "os.time.ntp.get",
        "os.time.ntp.set",
        "os.time.status",
        "os.time.timezone.check",
        "os.time.timezone.get",
        "os.time.timezone.set",
        "os.tool.exists",
        "os.tool.version_check",
    } <= names

    searched = [
        Path("docs/plugins/index.md"),
        Path("docs/plugins/linux-operations.md"),
        Path("docs/plugins/generated.md"),
        Path("docs/plugins/alternatives.md"),
        Path("docs/plugins/package-manager.md"),
        Path("docs/plugins/security.md"),
        Path("docs/plugins/users-groups-processes.md"),
        Path("examples/runbooks/RUNBOOK_INDEX.md"),
        *Path("examples/runbooks/runbooks").glob("*.check.yaml"),
    ]
    doc_old_names = [name for name in old_names if name != "login.defs"]
    offenders = []
    for path in searched:
        text = path.read_text(encoding="utf-8")
        for old_name in doc_old_names:
            pattern = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_name) + r"(?![A-Za-z0-9_.])")
            if pattern.search(text):
                offenders.append(f"{path}:{old_name}")
    assert offenders == []

def test_health_namespace_is_removed_from_public_documentation_and_runbooks():
    from automax.plugins.registry import build_builtin_registry

    assert not any(name.startswith("health.") for name in build_builtin_registry().names())

    searched = [
        Path("docs/plugins/index.md"),
        Path("docs/plugins/linux-operations.md"),
        Path("docs/plugins/generated.md"),
        Path("examples/runbooks/RUNBOOK_INDEX.md"),
        *Path("examples/runbooks/runbooks").glob("*.check.yaml"),
    ]
    offenders = [str(path) for path in searched if "health." in path.read_text(encoding="utf-8")]
    assert offenders == []

def test_resolver_namespace_is_not_public_plugin_surface():
    from automax.plugins.registry import build_builtin_registry

    names = set(build_builtin_registry().names())
    assert "network.dns.config" in names
    assert "network.dns.facts" in names
    assert not any(name.startswith("resolver.") for name in names)

    docs = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in ["docs/plugins/index.md", "docs/plugins/linux-operations.md", "docs/plugins/generated.md"]
    )
    assert ".".join(("resolver", "config")) not in docs
    assert ".".join(("resolver", "facts")) not in docs




def test_flat_network_resource_namespaces_are_not_public_plugin_surface():
    from automax.plugins.registry import build_builtin_registry

    old_names = [
        "network.bond",
        "network.bridge",
        "network.interface",
        "network.link_assert",
        "network.port_check",
        "network.route",
        "network.route_assert",
        "network.vlan",
    ]
    names = set(build_builtin_registry().names())
    assert not (names & set(old_names))
    assert {
        "network.link.bond",
        "network.link.bridge",
        "network.link.check",
        "network.link.facts",
        "network.link.interface",
        "network.link.vlan",
        "network.connectivity.port_check",
        "network.route.add",
        "network.route.check",
        "network.route.facts",
        "network.route.remove",
    } <= names

    searched = [
        Path("docs/plugins/index.md"),
        Path("docs/plugins/linux-operations.md"),
        Path("docs/plugins/generated.md"),
        Path("examples/runbooks/RUNBOOK_INDEX.md"),
        *Path("examples/runbooks/runbooks").glob("*.check.yaml"),
    ]
    offenders = []
    for path in searched:
        text = path.read_text(encoding="utf-8")
        for old_name in old_names:
            pattern = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_name) + r"(?![A-Za-z0-9_.])")
            if pattern.search(text):
                offenders.append(f"{path}:{old_name}")
    assert offenders == []

def test_top_level_firewall_namespaces_are_not_public_plugin_surface():
    import re

    from automax.plugins.registry import build_builtin_registry

    old_names = [
        "iptables.chain",
        "iptables.counter_assert",
        "iptables.delete",
        "iptables.exists_assert",
        "iptables.list",
        "iptables.policy",
        "iptables.restore",
        "iptables.rule",
        "iptables.save",
        "firewalld.forward_port",
        "firewalld.icmp_block",
        "firewalld.list",
        "firewalld.masquerade",
        "firewalld.port",
        "firewalld.reload",
        "firewalld.rich_rule",
        "firewalld.service",
        "firewalld.source",
        "firewalld.status",
        "firewalld.zone",
        "nftables.apply",
        "nftables.export",
        "nftables.list",
        "nftables.rollback_file",
        "nftables.ruleset_assert",
        "nftables.validate",
        "ufw.delete",
        "ufw.disable",
        "ufw.enable",
        "ufw.reset",
        "ufw.rule",
        "ufw.status",
    ]
    names = set(build_builtin_registry().names())
    assert not (names & set(old_names))
    assert {
        "network.firewall.firewalld.port",
        "network.firewall.iptables.rule",
        "network.firewall.nftables.apply",
        "network.firewall.ufw.rule",
    } <= names

    old_public_reference = re.compile(r"(?<!network[.]firewall[.])(" + "|".join(re.escape(name) for name in old_names) + r")")
    searched = [
        Path("docs/guides/firewall.md"),
        Path("docs/plugins/firewall.md"),
        Path("docs/plugins/index.md"),
        Path("docs/plugins/linux-operations.md"),
        Path("docs/plugins/generated.md"),
        Path("examples/runbooks/RUNBOOK_INDEX.md"),
        *Path("examples/runbooks/runbooks").glob("*.check.yaml"),
    ]
    offenders = []
    for path in searched:
        text = path.read_text(encoding="utf-8")
        if old_public_reference.search(text):
            offenders.append(str(path))
    assert offenders == []

def test_firewall_plugins_share_command_mixin_without_public_merge():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.firewall import (
        FirewallCommandMixin,
        FirewalldPortPlugin,
        FirewalldRichRulePlugin,
        FirewalldServicePlugin,
        IptablesRulePlugin,
        UfwRulePlugin,
    )
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    for name in ("network.firewall.firewalld.port", "network.firewall.firewalld.service", "network.firewall.firewalld.rich_rule", "network.firewall.ufw.rule", "network.firewall.iptables.rule"):
        assert isinstance(registry.get(name), FirewallCommandMixin)

    assert FirewalldPortPlugin().firewalld_scope({"runtime": True, "permanent": True}) == ""
    assert FirewalldPortPlugin().firewalld_scope({"permanent": True}) == "--permanent "
    assert "query-port=443/tcp" in FirewalldPortPlugin().manual_commands({"port": 443, "query_only": True}, context)[0]
    assert "add-service=ssh" in FirewalldServicePlugin().manual_commands({"service": "ssh"}, context)[0]
    assert "add-rich-rule=" in FirewalldRichRulePlugin().manual_commands({"rich_rule": "rule service name=ssh accept"}, context)[0]
    assert UfwRulePlugin().firewall_state({"state": "present"}) == "present"
    assert IptablesRulePlugin().firewall_state({"state": "absent"}) == "absent"

def test_builtin_plugins_do_not_patch_methods_after_class_definition():
    pattern = re.compile(r"\b\w+Plugin\.(execute|manual_commands|validate|_command|_command_parts|_content)\s*=")
    offenders = []
    for path in sorted(Path("src/automax/plugins").glob("*.py")):
        if path.name == "registry.py":
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{path}:{lineno}:{line.strip()}")

    assert offenders == []

def test_ambiguous_plugin_parameters_have_plugin_specific_schemas():
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    expected = {
        ("security.audit.search", "user"): ("string",),
        ("security.audit.search", "start"): ("string",),
        ("archive.compress", "source"): ("path",),
        ("archive.decompress", "archive"): ("path",),
        ("backup.restore", "archive"): ("boolean",),
        ("system.cron.entry.list", "user"): ("string",),
        ("network.firewall.firewalld.source", "source"): ("string",),
        ("security.selinux.boolean", "value"): ("boolean", "string"),
        ("system.kernel.sysctl.set", "value"): ("string",),
        ("system.service.start", "user"): ("boolean",),
        ("system.systemd.unit", "start"): ("boolean",),
        ("transfer.rsync", "archive"): ("boolean",),
    }

    for (plugin_name, param_name), expected_types in expected.items():
        schema = registry.get(plugin_name).parameter_schema[param_name]
        actual = schema.get("types", schema.get("type"))
        if isinstance(actual, str):
            actual = (actual,)
        assert tuple(actual) == expected_types

    registry.get("network.firewall.firewalld.source").validate({"source": "10.0.0.0/8"})
    registry.get("transfer.rsync").validate({"src": "/tmp/src", "dest": "/tmp/dest", "archive": True})

    firewalld_runbook = Path("examples/runbooks/runbooks/19-firewalld.check.yaml").read_text(encoding="utf-8")
    assert "source: 10.0.0.0/8" in firewalld_runbook
    assert "source: /var/log/app" not in firewalld_runbook

def test_docs_show_sudo_password_env_for_runs_and_capability_installs():
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [Path("README.md"), Path("docs/reference/cli.md"), Path("docs/guides/first-ssh-job.md")]
    )
    assert "automax run --job job.yaml --inventory inventory.yaml --sudo-password-env AUTOMAX_SUDO_PASSWORD" in docs
    assert "automax capabilities install --job job.yaml --inventory inventory.yaml --sudo-password-env AUTOMAX_SUDO_PASSWORD" in docs
    assert "automax capabilities install --job job.yaml --inventory inventory.yaml --sudo-password-env AUTOMAX_SUDO_PASSWORD --verbose" in docs
