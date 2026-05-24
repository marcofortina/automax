# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from automax.cli.cli import cli
from automax.core.engine import AutomaxEngine
from automax.core.models import ExecutionContext, Target
from automax.core.state import StateStore
from automax.plugins.base import PluginValidationError
import automax.plugins.fs_extra as fs_extra


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_validate_accepts_external_job_inventory_vars_and_file_secret(tmp_path: Path):
    secret = write(tmp_path / "secret.txt", "secret-value\n")
    job = write(
        tmp_path / "jobs" / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: external-job
tasks:
  - id: smoke
    targets: group:web
    steps:
      - id: local
        substeps:
          - id: echo
            use: local.command
            with:
              command: "echo {{ vars.message }} {{ secrets.demo }}"
""",
    )
    inventory = write(
        tmp_path / "inventory" / "lab.yaml",
        """
servers:
  web01:
    host: 127.0.0.1
    groups: [web]
""",
    )
    vars_file = write(tmp_path / "vars" / "lab.yaml", "vars:\n  message: hello\n")
    secrets_file = write(
        tmp_path / "secrets" / "lab.yaml",
        f"secrets:\n  demo:\n    provider: file\n    path: {secret}\n",
    )

    AutomaxEngine().validate(
        job_path=str(job),
        inventory_path=str(inventory),
        vars_path=str(vars_file),
        secrets_path=str(secrets_file),
    )


def test_cli_run_creates_state_for_local_job(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: local-smoke
tasks:
  - id: smoke
    targets: all
    steps:
      - id: local
        substeps:
          - id: echo
            use: local.command
            with:
              command: "printf ok"
            register:
              echoed: stdout.trim
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  controller:
    host: 127.0.0.1
""",
    )
    state_dir = tmp_path / "runs"

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--state-dir",
            str(state_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Run ID:" in result.output
    assert list(state_dir.glob("*/state.sqlite"))


def test_plan_prints_three_level_checkpoint_ids(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: plan-smoke
tasks:
  - id: t1
    targets: web
    tags: [install]
    steps:
      - id: s1
        substeps:
          - id: ss1
            tags: [safe]
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  web01:
    host: 127.0.0.1
    groups: [web]
""",
    )

    result = CliRunner().invoke(
        cli,
        ["plan", "--job", str(job), "--inventory", str(inventory)],
    )

    assert result.exit_code == 0, result.output
    assert "web01 task.t1:step.s1:substep.ss1" in result.output
    assert "tags=install,safe" in result.output


def test_state_store_lists_runs(tmp_path: Path):
    store = StateStore(tmp_path, "run-1")
    store.create_run(
        job_path="job.yaml",
        inventory_path="inventory.yaml",
        vars_path=None,
        secrets_path=None,
        metadata={},
    )

    runs = StateStore.list_all_runs(tmp_path)

    assert [run["run_id"] for run in runs] == ["run-1"]


def test_tags_and_skip_tags_filter_plan(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: tag-smoke
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: keep
            tags: [deploy]
            use: local.command
            with:
              command: "true"
          - id: skip
            tags: [dangerous]
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        [
            "plan",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--tags",
            "deploy,dangerous",
            "--skip-tags",
            "dangerous",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "substep.keep" in result.output
    assert "substep.skip" not in result.output


def test_parallel_strategy_runs_multiple_targets(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: parallel-smoke
strategy:
  mode: parallel
  max_parallel: 2
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: echo
            use: local.command
            with:
              command: "printf {{ server.name }}"
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

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 0, result.output
    assert "[OK] one" in result.output
    assert "[OK] two" in result.output


def test_failure_policy_continue_keeps_running_next_step(tmp_path: Path):
    marker = tmp_path / "marker"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: failure-policy-smoke
failurePolicy:
  onFailure: continue
tasks:
  - id: t1
    targets: all
    steps:
      - id: fail
        substeps:
          - id: bad
            use: local.command
            with:
              command: "false"
      - id: after
        substeps:
          - id: write_marker
            use: local.command
            with:
              command: "printf ok > {marker}"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 1, result.output
    assert marker.read_text(encoding="utf-8") == "ok"


def test_builtin_filesystem_plugins_are_registered():
    result = CliRunner().invoke(cli, ["plugins", "list"])

    assert result.exit_code == 0, result.output
    output_names = set(result.output.splitlines())
    for name in ("fs.cd", "fs.chmod", "fs.chown", "fs.mkdir"):
        assert name in output_names
    for alias in ("cd", "chmod", "chown", "mkdir"):
        assert alias not in output_names


def test_ssh_smoke_script_is_syntax_valid():
    script = Path("scripts/ssh-smoke.sh")
    assert script.exists()
    assert os.system(f"bash -n {script}") == 0


def test_new_macro_plugins_validate_in_job_yaml(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: macro-validate
failurePolicy:
  onFailure: continue
tasks:
  - id: macros
    targets: all
    steps:
      - id: filesystem
        substeps:
          - id: copy
            use: fs.copy
            with:
              src: /tmp/source.txt
              dest: /tmp/dest.txt
              overwrite: false
          - id: remove
            use: fs.remove
            with:
              path: /tmp/dest.txt
              force: true
          - id: tar
            use: archive.tar
            with:
              source: /tmp/source-dir
              dest: /tmp/source-dir.tar.gz
              compression: gzip
          - id: untar
            use: archive.untar
            with:
              archive: /tmp/source-dir.tar.gz
              dest: /tmp/extracted
              strip_components: 1
          - id: compress
            use: archive.compress
            with:
              source: /tmp/source.log
              dest: /tmp/source.log.gz
              compression: gzip
          - id: decompress
            use: archive.decompress
            with:
              archive: /tmp/source.log.gz
              dest: /tmp/source.log
              compression: gzip
          - id: zip
            use: archive.zip
            with:
              source: /tmp/source-dir
              dest: /tmp/source-dir.zip
          - id: unzip
            use: archive.unzip
            with:
              archive: /tmp/source-dir.zip
              dest: /tmp/unzipped
      - id: services
        substeps:
          - id: daemon_reload
            use: systemctl.daemon_reload
            with:
              sudo: true
          - id: start
            use: systemctl.start
            with:
              service: automax-demo.service
              sudo: true
          - id: stop
            use: systemctl.stop
            with:
              service: automax-demo.service
              sudo: true
          - id: restart
            use: systemctl.restart
            with:
              service: automax-demo.service
              sudo: true
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    AutomaxEngine().validate(job_path=str(job), inventory_path=str(inventory))


def test_builtin_macro_plugins_are_registered_with_canonical_names_only():
    result = CliRunner().invoke(cli, ["plugins", "list"])

    assert result.exit_code == 0, result.output
    output_names = set(result.output.splitlines())
    registry_names = set(AutomaxEngine().plugin_registry.names())

    assert output_names == registry_names
    assert "local_command" not in output_names
    assert "ssh_command" not in output_names
    assert "systemctl daemon reload" not in output_names


def test_filesystem_plugin_names_are_canonical():
    names = AutomaxEngine().plugin_registry.names()

    for name in (
        "fs.exists",
        "fs.stat",
        "fs.read",
        "fs.write",
        "fs.template",
        "fs.line",
        "fs.replace",
        "fs.move",
        "fs.symlink.create",
        "fs.symlink.remove",
        "fs.find",
    ):
        assert name in names

    assert "exists" not in names
    assert "template" not in names
    assert "fs.symlink" not in names


def test_symlink_plugins_are_conservative_and_canonical(monkeypatch):
    commands = []

    def fake_exec_remote(context, command, **kwargs):
        commands.append(command)
        return 0, "__AUTOMAX_CHANGED__\n", ""

    monkeypatch.setattr(fs_extra, "exec_remote", fake_exec_remote)
    context = ExecutionContext(
        run_id="run-1",
        dry_run=False,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="host", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )

    create_result = fs_extra.FsSymlinkCreatePlugin().execute(
        {"src": "/opt/app/releases/1", "dest": "/opt/app/current", "force": True},
        context,
    )
    remove_result = fs_extra.FsSymlinkRemovePlugin().execute(
        {"path": "/opt/app/current"},
        context,
    )

    assert create_result.ok and create_result.changed
    assert create_result.data == {"src": "/opt/app/releases/1", "dest": "/opt/app/current"}
    assert remove_result.ok and remove_result.changed
    assert remove_result.data == {"path": "/opt/app/current"}
    assert "allow_replace_non_symlink" in commands[0]
    assert "refusing to remove non-symlink path" in commands[1]

    with pytest.raises(PluginValidationError):
        fs_extra.FsSymlinkCreatePlugin().validate({"src": "/tmp/source", "dest": "/"})
    with pytest.raises(PluginValidationError):
        fs_extra.FsSymlinkRemovePlugin().validate({"path": "/"})


def test_package_manager_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    assert "pkg.install" in names
    assert "pkg.remove" in names
    assert "pkg.update_cache" in names
    assert "pkg.upgrade" in names
    assert "pkg.query" in names
    assert "apt.install" not in names


def test_extended_systemctl_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    for name in (
        "systemctl.reload",
        "systemctl.enable",
        "systemctl.disable",
        "systemctl.status",
        "systemctl.is_active",
        "systemctl.is_enabled",
        "systemctl.mask",
        "systemctl.unmask",
        "transfer.download",
        "transfer.sync",
        "transfer.upload",
        "user.create",
        "user.modify",
        "user.remove",
        "group.create",
        "group.remove",
    ):
        assert name in names

    assert "service.enable" not in names


def test_user_group_process_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    for name in (
        "user.create",
        "user.modify",
        "user.remove",
        "group.create",
        "group.remove",
        "process.kill",
        "process.wait",
    ):
        assert name in names

    assert "useradd" not in names
    assert "groupadd" not in names


def test_transfer_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    assert "transfer.upload" in names
    assert "transfer.download" in names
    assert "transfer.sync" in names
    assert "upload" not in names


def test_http_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    assert "http.request" in names
    assert "http.assert" in names
    assert "http.wait" in names
    assert "run_http_request" not in names



def test_wait_and_assert_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    for name in (
        "wait.tcp",
        "wait.command",
        "wait.file",
        "wait.path",
        "wait.process",
        "assert.tcp",
        "assert.command",
        "assert.file",
        "assert.path",
        "assert.disk",
    ):
        assert name in names

    assert "check.tcp" not in names
    assert "check.disk" not in names


def test_wait_assert_plugins_validate_in_job_yaml(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: wait-assert-validate
tasks:
  - id: checks
    targets: all
    steps:
      - id: remote_checks
        substeps:
          - id: wait_file
            use: wait.file
            with:
              path: /tmp/automax-ready
              state: absent
              timeout: 1
              interval: 1
          - id: assert_path
            use: assert.path
            with:
              path: /tmp
              type: directory
          - id: assert_command
            use: assert.command
            with:
              command: "printf ok"
              equals: ok
          - id: assert_disk
            use: assert.disk
            with:
              path: /
              min_free_mb: 1
      - id: controller_checks
        substeps:
          - id: wait_tcp
            use: wait.tcp
            with:
              host: 127.0.0.1
              port: 22
              timeout: 1
          - id: assert_tcp
            use: assert.tcp
            with:
              host: 127.0.0.1
              port: 22
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    AutomaxEngine().validate(job_path=str(job), inventory_path=str(inventory))



def test_fs_template_supports_explicit_values():
    plugin = AutomaxEngine().plugin_registry.get("fs.template")

    plugin.validate(
        {
            "src": "examples/next/templates/app.conf.j2",
            "dest": "/tmp/automax-app.conf",
            "values": {"app_name": "demo", "port": 8080},
        }
    )



def test_database_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    for name in (
        "db.sqlite.query",
        "db.postgres.query",
        "db.mysql.query",
        "db.oracle.query",
    ):
        assert name in names

    assert "database_operations" not in names
    assert "db.query" not in names


def test_sqlite_database_plugin_executes_transactional_statements(tmp_path: Path):
    from automax.core.models import ExecutionContext, Target

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
    database = tmp_path / "demo.sqlite"

    create = plugin.execute(
        {
            "connection": {"path": str(database)},
            "statements": [
                "CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT NOT NULL)",
                "INSERT INTO demo(name) VALUES ('automax')",
            ],
            "output": "none",
        },
        context,
    )
    assert create.ok, create.stderr

    select = plugin.execute(
        {
            "connection": {"path": str(database)},
            "query": "SELECT name FROM demo WHERE id = ?",
            "query_params": [1],
            "output": "scalar",
            "fetch": "one",
        },
        context,
    )

    assert select.ok, select.stderr
    assert select.data["scalar"] == "automax"
    assert select.stdout == "automax"


def test_database_plugins_validate_job_yaml(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: db-validate
tasks:
  - id: database
    targets: all
    steps:
      - id: sqlite
        substeps:
          - id: sqlite_query
            use: db.sqlite.query
            with:
              connection:
                path: /tmp/automax.sqlite
              query: "SELECT 1 AS value"
              output: scalar
      - id: optional_drivers
        substeps:
          - id: postgres_query
            use: db.postgres.query
            with:
              connection:
                database: app
                host: localhost
                user: app
                password: "{{ secrets.db_password | default('example') }}"
              query: "SELECT 1"
          - id: mysql_query
            use: db.mysql.query
            with:
              connection:
                database: app
                host: localhost
                user: app
                password: "{{ secrets.db_password | default('example') }}"
              query: "SELECT 1"
          - id: oracle_query
            use: db.oracle.query
            with:
              connection:
                dsn: localhost/FREEPDB1
                user: app
                password: "{{ secrets.db_password | default('example') }}"
              query: "SELECT 1 FROM dual"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    AutomaxEngine().validate(job_path=str(job), inventory_path=str(inventory))


def _extract_run_id(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("Run ID:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"Run ID not found in output: {output}")


def test_resume_skip_successful_does_not_rerun_completed_nodes(tmp_path: Path):
    good_marker = tmp_path / "good-count"
    trigger = tmp_path / "trigger"
    after_marker = tmp_path / "after-count"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: resume-skip-successful
failurePolicy:
  onFailure: stop_job
tasks:
  - id: deploy
    targets: all
    steps:
      - id: local
        substeps:
          - id: good
            use: local.command
            with:
              command: "printf x >> {good_marker}"
          - id: flaky
            use: local.command
            with:
              command: "test -f {trigger}"
          - id: after
            use: local.command
            with:
              command: "printf x >> {after_marker}"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    first = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir)],
    )
    assert first.exit_code == 1, first.output
    run_id = _extract_run_id(first.output)
    assert good_marker.read_text(encoding="utf-8") == "x"
    assert not after_marker.exists()

    trigger.write_text("ready", encoding="utf-8")
    second = CliRunner().invoke(
        cli,
        ["resume", run_id, "--state-dir", str(state_dir), "--skip-successful"],
    )

    assert second.exit_code == 0, second.output
    assert good_marker.read_text(encoding="utf-8") == "x"
    assert after_marker.read_text(encoding="utf-8") == "x"


def test_resume_only_failed_reruns_failed_nodes_only(tmp_path: Path):
    good_marker = tmp_path / "good-count"
    bad_marker = tmp_path / "bad-count"
    after_marker = tmp_path / "after-count"
    trigger = tmp_path / "trigger"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: resume-only-failed
failurePolicy:
  onFailure: continue
tasks:
  - id: deploy
    targets: all
    steps:
      - id: local
        substeps:
          - id: good
            use: local.command
            with:
              command: "printf x >> {good_marker}"
          - id: flaky
            use: local.command
            with:
              command: "printf x >> {bad_marker}; test -f {trigger}"
      - id: after
        substeps:
          - id: after
            use: local.command
            with:
              command: "printf x >> {after_marker}"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    first = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir)],
    )
    assert first.exit_code == 1, first.output
    run_id = _extract_run_id(first.output)
    assert good_marker.read_text(encoding="utf-8") == "x"
    assert bad_marker.read_text(encoding="utf-8") == "x"
    assert after_marker.read_text(encoding="utf-8") == "x"

    trigger.write_text("ready", encoding="utf-8")
    second = CliRunner().invoke(
        cli,
        ["resume", run_id, "--state-dir", str(state_dir), "--only-failed"],
    )

    assert second.exit_code == 0, second.output
    assert good_marker.read_text(encoding="utf-8") == "x"
    assert bad_marker.read_text(encoding="utf-8") == "xx"
    assert after_marker.read_text(encoding="utf-8") == "x"


def test_inherited_command_timeout_reaches_execution_context(tmp_path: Path, monkeypatch):
    seen: list[int | None] = []

    def fake_run(*args, **kwargs):
        seen.append(kwargs.get("timeout"))

        class Completed:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Completed()

    import automax.plugins.local_command as local_command

    monkeypatch.setattr(local_command.subprocess, "run", fake_run)
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: timeout-context
timeouts:
  command: 17
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: cmd
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 0, result.output
    assert seen == [17]


def test_substep_timeout_overrides_inherited_command_timeout(tmp_path: Path, monkeypatch):
    seen: list[int | None] = []

    def fake_run(*args, **kwargs):
        seen.append(kwargs.get("timeout"))

        class Completed:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Completed()

    import automax.plugins.local_command as local_command

    monkeypatch.setattr(local_command.subprocess, "run", fake_run)
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: timeout-context
timeouts:
  command: 17
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: cmd
            use: local.command
            with:
              command: "true"
              timeout: 3
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 0, result.output
    assert seen == [3]


def test_ssh_timeouts_are_merged_from_job_task_and_step():
    engine = AutomaxEngine()
    target = Target(name="web01", host="127.0.0.1", ssh={"connect_timeout": 99})
    resolved = engine._target_with_step_timeouts(
        target,
        {"timeouts": {"ssh_connect": 10, "ssh_banner": 11}},
        {"timeouts": {"ssh_connect": 20}},
        {"timeouts": {"ssh_auth": 30}},
    )

    assert resolved.ssh["connect_timeout"] == 20
    assert resolved.ssh["banner_timeout"] == 11
    assert resolved.ssh["auth_timeout"] == 30
    assert target.ssh["connect_timeout"] == 99


def test_invalid_timeout_key_is_rejected(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: bad-timeout
timeouts:
  socket: 10
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: cmd
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    with pytest.raises(ValueError, match="unsupported key"):
        AutomaxEngine().validate(job_path=str(job), inventory_path=str(inventory))


def test_nested_secret_values_are_masked_recursively():
    engine = AutomaxEngine()

    assert engine._mask_text(
        "token alpha-secret and password beta-secret",
        {"nested": {"token": "alpha-secret"}, "items": ["beta-secret"]},
    ) == "token *** and password ***"


def test_remote_connection_errors_are_masked_in_state(tmp_path: Path):
    from contextlib import contextmanager

    class FailingSshManager:
        @contextmanager
        def connect(self, target):
            raise RuntimeError("cannot connect with alpha-secret")
            yield  # pragma: no cover

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: masked-connect-error
tasks:
  - id: remote
    targets: all
    steps:
      - id: s1
        substeps:
          - id: cmd
            use: remote.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  host:\n    host: 127.0.0.1\n")
    secrets = write(tmp_path / "secrets.yaml", "secrets:\n  token:\n    provider: env\n    name: AUTOMAX_MASK_TEST\n")
    os.environ["AUTOMAX_MASK_TEST"] = "alpha-secret"
    state_dir = tmp_path / "runs"

    rc = AutomaxEngine(ssh_manager=FailingSshManager()).run(
        job_path=str(job),
        inventory_path=str(inventory),
        secrets_path=str(secrets),
        state_dir=str(state_dir),
    )

    assert rc == 1
    run_id = next(state_dir.iterdir()).name
    store = StateStore(state_dir, run_id)
    with store.connect() as conn:
        row = conn.execute("SELECT message FROM nodes WHERE run_id = ?", (run_id,)).fetchone()
    assert row is not None
    assert row["message"] == "cannot connect with ***"


def test_plugin_metadata_contains_structured_parameters_and_examples():
    metadata = AutomaxEngine().plugin_registry.describe("fs.template")

    assert metadata["category"] == "fs"
    assert any(item["name"] == "src" and item["required"] for item in metadata["parameters"])
    assert any(item["name"] == "sudo" and item["default"] is False for item in metadata["parameters"])
    assert metadata["examples"]
    assert metadata["result_fields"]["data.dest"] == "Remote destination path"


def test_plugins_describe_json_outputs_structured_metadata():
    result = CliRunner().invoke(cli, ["plugins", "describe", "fs.template", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name"] == "fs.template"
    assert payload["category"] == "fs"
    assert any(item["name"] == "dest" for item in payload["parameters"])


def test_plugin_describe_human_output_includes_rich_metadata():
    result = CliRunner().invoke(cli, ["plugins", "describe", "fs.template"])

    assert result.exit_code == 0, result.output
    assert "Category: fs" in result.output
    assert "Parameters:" in result.output
    assert "src (required, path)" in result.output
    assert "Examples:" in result.output


def test_substep_artifacts_capture_masked_stdout_and_data(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AUTOMAX_ARTIFACT_SECRET", "artifact-secret")
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: artifact-capture
tasks:
  - id: collect
    targets: all
    steps:
      - id: local
        substeps:
          - id: command
            use: local.command
            with:
              command: "printf artifact-secret"
            artifacts:
              stdout: "{{ target.name }}/stdout.txt"
              data: data.json
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    secrets = write(
        tmp_path / "secrets.yaml",
        "secrets:\n  token:\n    provider: env\n    name: AUTOMAX_ARTIFACT_SECRET\n",
    )
    state_dir = tmp_path / "runs"

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets),
            "--state-dir",
            str(state_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    run_id = _extract_run_id(result.output)
    store = StateStore(state_dir, run_id)
    artifacts = store.list_artifacts()
    assert {item["kind"] for item in artifacts} == {"stdout", "data"}
    stdout_artifact = next(item for item in artifacts if item["kind"] == "stdout")
    assert Path(stdout_artifact["path"]).read_text(encoding="utf-8") == "***"
    assert stdout_artifact["name"] == "controller/stdout.txt"

    listed = CliRunner().invoke(cli, ["artifacts", "list", run_id, "--state-dir", str(state_dir)])
    assert listed.exit_code == 0, listed.output
    assert "controller/stdout.txt" in listed.output

    path_result = CliRunner().invoke(cli, ["artifacts", "path", run_id, "--state-dir", str(state_dir)])
    assert path_result.exit_code == 0, path_result.output
    assert Path(path_result.output.strip()).is_dir()


def test_artifact_path_traversal_fails_the_substep(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: artifact-path-traversal
tasks:
  - id: collect
    targets: all
    steps:
      - id: local
        substeps:
          - id: command
            use: local.command
            with:
              command: "printf ok"
            artifacts:
              stdout: ../unsafe.txt
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 1, result.output
    assert "artifact capture failed" in result.output


def test_runs_show_displays_summary_and_target_status(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: runs-show-success
failurePolicy:
  onFailure: continue
tasks:
  - id: inspect
    targets: all
    steps:
      - id: local
        substeps:
          - id: ok
            use: local.command
            with:
              command: "printf ok"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    run = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir)],
    )
    assert run.exit_code == 0, run.output
    run_id = _extract_run_id(run.output)

    shown = CliRunner().invoke(cli, ["runs", "show", run_id, "--state-dir", str(state_dir)])

    assert shown.exit_code == 0, shown.output
    assert f"Run: {run_id}" in shown.output
    assert "Summary:" in shown.output
    assert "targets: 1" in shown.output
    assert "nodes: 1" in shown.output
    assert "Targets:" in shown.output
    assert "controller success" in shown.output


def test_failed_run_summary_and_runs_show_failed_filter(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: runs-show-failed
failurePolicy:
  onFailure: continue
tasks:
  - id: inspect
    targets: all
    steps:
      - id: local
        substeps:
          - id: good
            use: local.command
            with:
              command: "true"
          - id: bad
            use: local.command
            with:
              command: "false"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    run = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir)],
    )

    assert run.exit_code == 1, run.output
    assert "Automax run failed" in run.output
    assert "Summary:" in run.output
    assert "Resume options:" in run.output
    run_id = _extract_run_id(run.output)

    shown = CliRunner().invoke(
        cli,
        ["runs", "show", run_id, "--state-dir", str(state_dir), "--failed"],
    )

    assert shown.exit_code == 0, shown.output
    assert "Failed nodes:" in shown.output
    assert "task.inspect:step.local:substep.bad" in shown.output
    assert "Nodes:" in shown.output
    assert "substep.good" not in shown.output


def test_runs_show_json_includes_summary_and_filtered_nodes(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: runs-show-json
failurePolicy:
  onFailure: continue
tasks:
  - id: inspect
    targets: all
    steps:
      - id: local
        substeps:
          - id: ok
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    run = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir)],
    )
    assert run.exit_code == 0, run.output
    run_id = _extract_run_id(run.output)

    shown = CliRunner().invoke(
        cli,
        ["runs", "show", run_id, "--state-dir", str(state_dir), "--server", "controller", "--json"],
    )

    assert shown.exit_code == 0, shown.output
    payload = json.loads(shown.output)
    assert payload["run"]["run_id"] == run_id
    assert payload["targets_total"] == 1
    assert payload["status_counts"]["success"] == 1
    assert payload["nodes"][0]["target"] == "controller"


def test_builtin_plugin_metadata_is_complete():
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    assert registry.names()
    for plugin in registry.describe_all():
        assert plugin["description"].strip(), plugin["name"]
        assert plugin["examples"], plugin["name"]
        assert plugin["result_fields"], plugin["name"]
        parameter_names = [parameter["name"] for parameter in plugin["parameters"]]
        assert parameter_names == list(plugin["required_params"]) + list(plugin["optional_params"])
        for parameter in plugin["parameters"]:
            assert parameter["type"] != "any", (plugin["name"], parameter)
            assert parameter["description"].strip(), (plugin["name"], parameter)
            assert parameter["description"].strip() != "-", (plugin["name"], parameter)


def test_generated_plugin_reference_is_in_sync():
    from automax.core.plugin_docs import render_plugin_reference
    from automax.plugins.registry import build_builtin_registry

    expected = render_plugin_reference(build_builtin_registry().describe_all())
    generated = Path("docs/plugins/generated.md").read_text(encoding="utf-8")

    assert generated == expected
    assert "`any`" not in generated
    assert "| - |" not in generated


def test_plugins_describe_uses_complete_metadata():
    result = CliRunner().invoke(cli, ["plugins", "describe", "archive.tar"])

    assert result.exit_code == 0, result.output
    assert "source (required, path): Remote source path to archive." in result.output
    assert "Result fields:" in result.output
    assert "Examples:" in result.output


def test_extended_ssh_smoke_script_covers_runtime_plugin_families():
    script = Path("scripts/ssh-smoke.sh").read_text(encoding="utf-8")
    required_snippets = [
        "fs.write",
        "fs.read",
        "fs.exists",
        "fs.stat",
        "fs.line",
        "fs.replace",
        "fs.move",
        "fs.symlink.create",
        "fs.symlink.remove",
        "archive.tar",
        "archive.untar",
        "archive.compress",
        "archive.decompress",
        "archive.zip",
        "archive.unzip",
        "transfer.upload",
        "transfer.download",
        "transfer.sync",
        "wait.command",
        "wait.file",
        "wait.path",
        "wait.process",
        "assert.command",
        "assert.file",
        "assert.path",
        "assert.disk",
        "assert.tcp",
        "systemctl.status",
        "pkg.query",
        "user.create",
        "group.create",
        "process.kill",
    ]
    for snippet in required_snippets:
        assert snippet in script
    assert "AUTOMAX_SSH_SMOKE_PRIVILEGED" in script
    assert "AUTOMAX_SSH_SMOKE_SYSTEMD_SERVICE" in script
    assert "AUTOMAX_SSH_SMOKE_PKG" in script
    assert "exit 77" in script


def test_ssh_smoke_documentation_is_linked():
    guide = Path("docs/guides/ssh-smoke.md").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Extended SSH smoke" in guide
    assert "AUTOMAX_SSH_SMOKE_PRIVILEGED" in guide
    assert "SSH Smoke: guides/ssh-smoke.md" in mkdocs
    assert "docs/guides/ssh-smoke.md" in readme

def test_validate_strict_rejects_unknown_plugin_parameter(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: strict-validation
tasks:
  - id: smoke
    targets: all
    steps:
      - id: local
        substeps:
          - id: echo
            use: local.command
            with:
              command: "true"
              typo: "bad"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["validate", "--strict", "--job", str(job), "--inventory", str(inventory)],
    )

    assert result.exit_code != 0
    assert "unknown params: typo" in result.output


def test_init_creates_external_workspace(tmp_path: Path):
    workspace = tmp_path / "workspace"

    result = CliRunner().invoke(cli, ["init", str(workspace)])

    assert result.exit_code == 0, result.output
    assert (workspace / "jobs" / "local-smoke.yaml").exists()
    assert (workspace / "inventory" / "local.yaml").exists()
    assert (workspace / "vars" / "local.yaml").exists()
    assert (workspace / "secrets" / "local.example.yaml").exists()

    validate = CliRunner().invoke(
        cli,
        [
            "validate",
            "--strict",
            "--job",
            str(workspace / "jobs" / "local-smoke.yaml"),
            "--inventory",
            str(workspace / "inventory" / "local.yaml"),
            "--vars",
            str(workspace / "vars" / "local.yaml"),
        ],
    )
    assert validate.exit_code == 0, validate.output


def test_doctor_reports_controller_environment(tmp_path: Path):
    result = CliRunner().invoke(cli, ["doctor", "--state-dir", str(tmp_path / "runs")])

    assert result.exit_code == 0, result.output
    assert "Automax doctor" in result.output
    assert "python:" in result.output
    assert "plugins:" in result.output


def test_schema_export_emits_json_schema(tmp_path: Path):
    result = CliRunner().invoke(cli, ["schema", "export", "--kind", "job", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert payload["properties"]["apiVersion"]["const"] == "automax.io/v1"

    output = tmp_path / "schemas" / "all.json"
    result = CliRunner().invoke(
        cli,
        [
            "schema",
            "export",
            "--kind",
            "all",
            "--format",
            "json",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Wrote" in result.output
    exported = json.loads(output.read_text(encoding="utf-8"))
    assert sorted(exported["required"]) == ["inventory", "job", "secrets", "vars"]


def test_plan_format_json_outputs_machine_readable_plan(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: json-plan
tasks:
  - id: smoke
    targets: all
    steps:
      - id: local
        substeps:
          - id: echo
            tags: [safe]
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["plan", "--job", str(job), "--inventory", str(inventory), "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["nodes"][0]["node_id"] == "task.smoke:step.local:substep.echo"
    assert payload["nodes"][0]["plugin"] == "local.command"
    assert payload["nodes"][0]["tags"] == ["safe"]


def test_run_format_json_outputs_final_summary_only(tmp_path: Path):
    marker = tmp_path / "marker"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: json-run
tasks:
  - id: smoke
    targets: all
    steps:
      - id: local
        substeps:
          - id: echo
            use: local.command
            with:
              command: "printf ok > {marker}"
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
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "success"
    assert payload["summary"]["success"] == 1
    assert payload["summary"]["failed"] == 0
    assert payload["resume"]["default"].startswith("automax resume ")
    assert marker.read_text(encoding="utf-8") == "ok"


def test_dynamic_file_inventory_provider_resolves_relative_path(tmp_path: Path):
    included = write(
        tmp_path / "inventories" / "generated.yaml",
        """
servers:
  dyn01:
    host: 127.0.0.1
    groups: [dynamic]
""",
    )
    wrapper = write(
        tmp_path / "inventories" / "wrapper.yaml",
        """
inventory:
  provider: file
  path: generated.yaml
""",
    )
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: dynamic-file
 tasks: []
""".replace(" tasks", "tasks"),
    )
    # Use plan through a real job so the engine exercises dynamic loading.
    job.write_text(
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: dynamic-file
tasks:
  - id: t1
    targets: dynamic
    steps:
      - id: s1
        substeps:
          - id: ss1
            use: local.command
            with:
              command: "true"
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["plan", "--job", str(job), "--inventory", str(wrapper)],
    )

    assert result.exit_code == 0, result.output
    assert "dyn01 task.t1:step.s1:substep.ss1" in result.output
    assert included.exists()


def test_dynamic_command_inventory_provider_uses_stdout_yaml(tmp_path: Path):
    script = write(
        tmp_path / "inventory_command.py",
        """
import sys
sys.stdout.write('servers:\\n  cmd01:\\n    host: 127.0.0.1\\n    groups: [cmd]\\n')
""",
    )
    wrapper = write(
        tmp_path / "inventory.yaml",
        f"""
inventory:
  provider: command
  command: ["{sys.executable}", "{script}"]
  timeout: 5
""",
    )
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: dynamic-command
tasks:
  - id: t1
    targets: cmd
    steps:
      - id: s1
        substeps:
          - id: ss1
            use: local.command
            with:
              command: "true"
""",
    )

    result = CliRunner().invoke(
        cli,
        ["plan", "--job", str(job), "--inventory", str(wrapper)],
    )

    assert result.exit_code == 0, result.output
    assert "cmd01 task.t1:step.s1:substep.ss1" in result.output


def test_command_secret_provider_resolves_stdout_and_masks_value(tmp_path: Path):
    secret_script = write(
        tmp_path / "secret.py",
        """
print('command-secret-value')
""",
    )
    secrets_file = write(
        tmp_path / "secrets.yaml",
        f"""
secrets:
  token:
    provider: command
    command: ["{sys.executable}", "{secret_script}"]
    timeout: 5
""",
    )
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: command-secret
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: ss1
            use: local.command
            with:
              command: "printf '{{ secrets.token }}'"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
            "--state-dir",
            str(state_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "command-secret-value" not in result.output
    state_files = list(state_dir.glob("*/state.sqlite"))
    assert state_files


def test_schema_export_includes_dynamic_inventory_and_command_secret_provider():
    result = CliRunner().invoke(cli, ["schema", "export", "--kind", "all", "--format", "json"])

    assert result.exit_code == 0, result.output
    exported = json.loads(result.output)
    inventory_schema = json.dumps(exported["properties"]["inventory"])
    secrets_schema = json.dumps(exported["properties"]["secrets"])
    assert "command" in inventory_schema
    assert "http" in inventory_schema
    assert "command" in secrets_schema
    assert "env" in secrets_schema
    assert "file" in secrets_schema


def test_cli_explain_outputs_targets_and_resume_points(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: explain-smoke
tasks:
  - id: deploy
    targets: all
    steps:
      - id: prepare
        substeps:
          - id: echo
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(cli, ["explain", "--job", str(job), "--inventory", str(inventory)])

    assert result.exit_code == 0, result.output
    assert "Job: explain-smoke" in result.output
    assert "Task deploy" in result.output
    assert "task.deploy:step.prepare:substep.echo" in result.output


def test_cli_graph_outputs_mermaid_and_svg(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: graph-smoke
tasks:
  - id: deploy
    targets: all
    steps:
      - id: prepare
        substeps:
          - id: echo
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    mermaid = CliRunner().invoke(cli, ["graph", "--job", str(job), "--inventory", str(inventory)])
    assert mermaid.exit_code == 0, mermaid.output
    assert "flowchart TD" in mermaid.output
    assert "local.command" in mermaid.output

    svg_path = tmp_path / "job.svg"
    svg = CliRunner().invoke(
        cli,
        ["graph", "--job", str(job), "--inventory", str(inventory), "--format", "svg", "--output", str(svg_path)],
    )
    assert svg.exit_code == 0, svg.output
    assert svg_path.read_text(encoding="utf-8").startswith("<svg")


def test_cli_runbook_export_writes_markdown(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: runbook-smoke
tasks:
  - id: deploy
    targets: all
    steps:
      - id: prepare
        substeps:
          - id: echo
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    runbook_path = tmp_path / "runbook.md"

    result = CliRunner().invoke(
        cli,
        ["runbook", "export", "--job", str(job), "--inventory", str(inventory), "--output", str(runbook_path)],
    )

    assert result.exit_code == 0, result.output
    content = runbook_path.read_text(encoding="utf-8")
    assert "# runbook-smoke runbook" in content
    assert "Resume checkpoint: `task.deploy:step.prepare:substep.echo`" in content


def test_cli_run_lock_rejects_concurrent_target_lock(tmp_path: Path):
    from automax.core.locks import LockManager

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: lock-smoke
tasks:
  - id: smoke
    targets: all
    steps:
      - id: local
        substeps:
          - id: echo
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"
    manager = LockManager.for_state_dir(state_dir)
    held = manager.acquire_many(["target:controller"])
    try:
        result = CliRunner().invoke(
            cli,
            ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir), "--lock", "--lock-scope", "target"],
        )
    finally:
        manager.release_many(held)

    assert result.exit_code != 0
    assert "lock already held" in result.output

def test_retry_policy_retries_until_success_and_records_attempts(tmp_path: Path):
    counter = tmp_path / "retry-count"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: retry-smoke
tasks:
  - id: retry
    targets: all
    steps:
      - id: local
        substeps:
          - id: flaky
            use: local.command
            retry:
              attempts: 3
              delay: 0
            with:
              command: "python -c \\\"from pathlib import Path; p=Path(r'{counter}'); n=int(p.read_text() or '0') if p.exists() else 0; p.write_text(str(n+1)); raise SystemExit(0 if n >= 1 else 1)\\\""
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir)],
    )

    assert result.exit_code == 0, result.output
    assert "[RETRY] controller task.retry:step.local:substep.flaky attempt=1/3" in result.output
    assert counter.read_text(encoding="utf-8") == "2"
    run_id = _extract_run_id(result.output)
    store = StateStore(state_dir, run_id)
    nodes = store.list_nodes()
    assert nodes[0]["output"]["data"]["attempt"] == 2
    assert len(nodes[0]["output"]["data"]["attempts"]) == 2


def test_retry_policy_respects_retry_on_rc(tmp_path: Path):
    counter = tmp_path / "retry-count"
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: retry-on-rc
tasks:
  - id: retry
    targets: all
    steps:
      - id: local
        substeps:
          - id: no_retry
            use: local.command
            retry:
              attempts: 3
              delay: 0
              retry_on_rc: [2]
            with:
              command: "python -c \\\"from pathlib import Path; p=Path(r'{counter}'); n=int(p.read_text() or '0') if p.exists() else 0; p.write_text(str(n+1)); raise SystemExit(1)\\\""
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 1, result.output
    assert "[RETRY]" not in result.output
    assert counter.read_text(encoding="utf-8") == "1"


def test_error_policy_accepts_expected_nonzero_rc_as_warning_and_continues(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: accepted-error-policy
tasks:
  - id: verify
    targets: all
    steps:
      - id: cluvfy
        substeps:
          - id: runcluvfy
            use: local.command
            with:
              command:
                - {sys.executable!r}
                - -c
                - "import sys; print('PRVF-5436 expected NTP diagnostic'); sys.exit(1)"
            errorPolicy:
              acceptedRc: [1, 2, 3]
              expected:
                - stream: combined
                  pattern: "PRVF-5436.*NTP"
                  reason: "chrony is managed externally"
              unmatched: fail
              acceptedStatus: warning
          - id: after_warning
            use: local.command
            with:
              command:
                - {sys.executable!r}
                - -c
                - "print('continued')"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    state_dir = tmp_path / "runs"

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(state_dir)],
    )

    assert result.exit_code == 0, result.output
    assert "[WARN] controller task.verify:step.cluvfy:substep.runcluvfy rc=1" in result.output
    assert "[OK] controller task.verify:step.cluvfy:substep.after_warning rc=0" in result.output
    run_id = next(state_dir.iterdir()).name
    summary = StateStore(state_dir, run_id).summarize()
    assert summary["status_counts"].get("warning") == 1
    assert summary["status_counts"].get("success") == 1
    assert summary["run"]["status"] == "warning"
    warning_node = summary["warning_nodes"][0]
    assert warning_node["output"]["data"]["errorPolicy"]["accepted"] is True


def test_error_policy_keeps_unexpected_output_failed(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: unexpected-error-policy
tasks:
  - id: verify
    targets: all
    steps:
      - id: cluvfy
        substeps:
          - id: runcluvfy
            use: local.command
            with:
              command:
                - {sys.executable!r}
                - -c
                - "import sys; print('ORA-00600 unexpected'); sys.exit(1)"
            errorPolicy:
              acceptedRc: [1]
              expected:
                - pattern: "PRVF-5436.*NTP"
              unmatched: fail
          - id: should_not_run
            use: local.command
            with:
              command:
                - {sys.executable!r}
                - -c
                - "print('must not run')"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 1, result.output
    assert "[FAILED] controller task.verify:step.cluvfy:substep.runcluvfy rc=1" in result.output
    assert "should_not_run" not in result.output


def test_error_policy_validate_strict_accepts_expected_fields(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: strict-error-policy
errorPolicy:
  acceptedRc: [1]
  expected:
    - stream: combined
      pattern: "EXPECTED"
      reason: "demo"
  fail:
    - stream: stderr
      pattern: "FATAL"
  unmatched: fail
  acceptedStatus: warning
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: ss1
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    AutomaxEngine().validate(job_path=str(job), inventory_path=str(inventory), strict=True)


def test_operator_view_helpers_resolve_and_render_selected_job(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: operator-helpers
vars:
  message: hello
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: keep
            tags: [deploy]
            use: local.command
            with:
              command: "printf {{ vars.message }}"
          - id: skip
            tags: [skipme]
            use: local.command
            with:
              command: "false"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )
    engine = AutomaxEngine()

    resolved = engine.resolve_job_context(
        job_path=str(job),
        inventory_path=str(inventory),
        tags=["deploy"],
    )
    rendered = list(engine.iter_rendered_plan_items(resolved))

    assert resolved.job["metadata"]["name"] == "operator-helpers"
    assert [item["node_id"] for item in resolved.plan] == ["task.t1:step.s1:substep.keep"]
    assert rendered[0]["plugin_name"] == "local.command"
    assert rendered[0]["params"]["command"] == "printf hello"


def test_inventory_show_is_scoped_to_resolved_job(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: inventory-show
tasks:
  - id: t1
    targets: group:web
    steps:
      - id: s1
        substeps:
          - id: keep
            tags: [deploy]
            use: local.command
            with:
              command: "true"
          - id: skip
            tags: [skipme]
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  web01:
    host: 10.0.0.11
    user: deploy
    groups: [web, production]
  db01:
    host: 10.0.0.21
    groups: [db, production]
""",
    )

    result = CliRunner().invoke(
        cli,
        [
            "inventory",
            "show",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--tags",
            "deploy",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Job: inventory-show" in result.output
    assert "web01  10.0.0.11:22  user=deploy groups=web,production nodes=1" in result.output
    assert "db01" not in result.output


def test_inventory_show_json(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: inventory-json
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: echo
            use: local.command
            with:
              command: "true"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )

    result = CliRunner().invoke(
        cli,
        [
            "inventory",
            "show",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["target_count"] == 1
    assert payload["targets"][0]["name"] == "controller"


def test_secrets_check_reports_only_selected_job_secret_values_masked(
    tmp_path: Path, monkeypatch
):
    secret_file = write(tmp_path / "token.txt", "super-secret-token\n")
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: secrets-check
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: selected
            tags: [deploy]
            use: local.command
            with:
              command: "printf {{ secrets.deploy_token }}"
          - id: skipped
            tags: [skipme]
            use: local.command
            with:
              command: "printf {{ secrets.skipped_token }}"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )
    secrets_file = write(
        tmp_path / "secrets.yaml",
        f"""
secrets:
  deploy_token:
    provider: file
    path: {secret_file}
  skipped_token:
    provider: env
    name: AUTOMAX_SKIPPED_TOKEN
  unused_token:
    provider: env
    name: AUTOMAX_UNUSED_TOKEN
""",
    )
    monkeypatch.delenv("AUTOMAX_SKIPPED_TOKEN", raising=False)
    monkeypatch.delenv("AUTOMAX_UNUSED_TOKEN", raising=False)

    result = CliRunner().invoke(
        cli,
        [
            "secrets",
            "check",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
            "--tags",
            "deploy",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "deploy_token  file  OK  used  resolved" in result.output
    assert "skipped_token" not in result.output
    assert "unused_token" not in result.output
    assert "super-secret-token" not in result.output


def test_secrets_check_fails_for_missing_selected_job_secret(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: missing-secret
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: echo
            use: local.command
            with:
              command: "printf {{ secrets.missing_token }}"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )
    secrets_file = write(tmp_path / "secrets.yaml", "secrets: {}\n")

    result = CliRunner().invoke(
        cli,
        [
            "secrets",
            "check",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
        ],
    )

    assert result.exit_code != 0
    assert "missing_token  undeclared  MISSING  used" in result.output
    assert "one or more secrets failed checks" in result.output


def test_plan_check_prints_job_scoped_dry_run_preview(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: check-preview
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: echo
            use: local.command
            with:
              command: "printf {{ secrets.token }}"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )
    secrets_file = write(tmp_path / "secrets.yaml", "secrets:\n  token: super-secret\n")

    result = CliRunner().invoke(
        cli,
        [
            "plan",
            "--check",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Job: check-preview" in result.output
    assert "CHECK controller task.t1:step.s1:substep.echo local.command" in result.output
    assert "super-secret" not in result.output
    assert "***" in result.output


def test_run_check_does_not_create_state(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: run-check-preview
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: echo
            use: local.command
            with:
              command: "printf ok"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )
    state_dir = tmp_path / "runs"

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--check",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--state-dir",
            str(state_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Check mode preview" in result.output
    assert not state_dir.exists()


def test_plan_diff_prints_fs_write_preview_with_masked_secrets(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: diff-preview
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: write
            use: fs.write
            with:
              path: /etc/demo.conf
              content: "token={{ secrets.token }}\n"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )
    secrets_file = write(tmp_path / "secrets.yaml", "secrets:\n  token: super-secret\n")

    result = CliRunner().invoke(
        cli,
        [
            "plan",
            "--diff",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Job: diff-preview" in result.output
    assert "# controller task.t1:step.s1:substep.write fs.write /etc/demo.conf" in result.output
    assert "+++ /etc/demo.conf (desired)" in result.output
    assert "+token=***" in result.output
    assert "super-secret" not in result.output


def test_plan_diff_renders_fs_template_preview(tmp_path: Path):
    template = write(tmp_path / "template.conf.j2", "message={{ values.message }}\n")
    job = write(
        tmp_path / "job.yaml",
        f"""
apiVersion: automax.io/v1
kind: Job
metadata:
  name: template-diff
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: template
            use: fs.template
            with:
              src: {template}
              dest: /etc/template.conf
              values:
                message: hello
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )

    result = CliRunner().invoke(
        cli,
        ["plan", "--diff", "--job", str(job), "--inventory", str(inventory)],
    )

    assert result.exit_code == 0, result.output
    assert "+message=hello" in result.output


def test_commands_render_prints_manual_commands_and_masks_secrets(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: manual-commands
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: local
            use: local.command
            with:
              command: "printf {{ secrets.token }}"
          - id: cleanup
            use: fs.remove
            with:
              path: /tmp/demo
              recursive: true
              force: true
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )
    secrets_file = write(tmp_path / "secrets.yaml", "secrets:\n  token: super-secret\n")

    result = CliRunner().invoke(
        cli,
        [
            "commands",
            "render",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "checkpoint=task.t1:step.s1:substep.local" in result.output
    assert "printf ***" in result.output
    assert "super-secret" not in result.output
    assert "test ! -e /tmp/demo || { rm -rf /tmp/demo" in result.output


def test_commands_render_json_marks_unavailable_plugins(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: manual-json
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: stat
            use: fs.stat
            with:
              path: /tmp/demo
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        "servers:\n  controller:\n    host: 127.0.0.1\n",
    )

    result = CliRunner().invoke(
        cli,
        [
            "commands",
            "render",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["nodes"][0]["available"] is False
    assert payload["nodes"][0]["commands"] == []


def test_vars_render_prints_target_context_and_masks_secrets(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: vars-render
vars:
  app_port: 8080
tasks:
  - id: deploy
    targets: web
    steps:
      - id: render
        substeps:
          - id: command
            use: local.command
            with:
              command: "printf {{ vars.app_port }} {{ vars.role }} {{ secrets.token }}"
""",
    )
    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  web01:
    host: 127.0.0.1
    groups: [web]
    vars:
      role: frontend
""",
    )
    secrets_file = write(tmp_path / "secrets.yaml", "secrets:\n  token: super-secret\n")

    result = CliRunner().invoke(
        cli,
        [
            "vars",
            "render",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
            "--var",
            "app_port=9090",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Job: vars-render" in result.output
    assert "Target web01 127.0.0.1:22 groups=web" in result.output
    assert "app_port: \"9090\"" in result.output
    assert "role: \"frontend\"" in result.output
    assert "token: ***" in result.output
    assert "task.deploy:step.render:substep.command local.command" in result.output
    assert "super-secret" not in result.output


def test_vars_render_json_masks_secret_values(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: vars-render-json
tasks:
  - id: deploy
    targets: all
    steps:
      - id: render
        substeps:
          - id: command
            use: local.command
            with:
              command: "printf {{ secrets.token }}"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    secrets_file = write(tmp_path / "secrets.yaml", "secrets:\n  token: super-secret\n")

    result = CliRunner().invoke(
        cli,
        [
            "vars",
            "render",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--secrets",
            str(secrets_file),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["targets"][0]["secrets"] == {"token": "***"}
    assert "super-secret" not in result.output


def test_ssh_known_hosts_scan_prints_fingerprints_and_writes_output(tmp_path: Path, monkeypatch):
    from automax.core import known_hosts as known_hosts_core

    def fake_run(command, **kwargs):
        assert command[:6] == ["ssh-keyscan", "-T", "5", "-p", "22", "example.com"]

        class Completed:
            returncode = 0
            stdout = "example.com ssh-ed25519 QUJDREVGR0g=\n"
            stderr = ""

        return Completed()

    monkeypatch.setattr(known_hosts_core.subprocess, "run", fake_run)
    output = tmp_path / "known_hosts"

    result = CliRunner().invoke(
        cli,
        [
            "ssh",
            "known-hosts",
            "scan",
            "--host",
            "example.com",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Verify these fingerprints" in result.output
    assert "example.com:22  ssh-ed25519  SHA256:" in result.output
    assert output.read_text(encoding="utf-8") == "example.com ssh-ed25519 QUJDREVGR0g=\n"


def test_ssh_known_hosts_scan_uses_inventory_selection(tmp_path: Path, monkeypatch):
    from automax.core import known_hosts as known_hosts_core

    seen_hosts = []

    def fake_run(command, **kwargs):
        seen_hosts.append(command[-1])

        class Completed:
            returncode = 0
            stdout = f"{command[-1]} ssh-rsa QUJDREVGR0g=\n"
            stderr = ""

        return Completed()

    monkeypatch.setattr(known_hosts_core.subprocess, "run", fake_run)
    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  web01:
    host: 192.0.2.11
    groups: [web]
  db01:
    host: 192.0.2.21
    groups: [db]
""",
    )

    result = CliRunner().invoke(
        cli,
        [
            "ssh",
            "known-hosts",
            "scan",
            "--inventory",
            str(inventory),
            "--limit",
            "web",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert seen_hosts == ["192.0.2.11"]
    assert payload["entries"][0]["host"] == "192.0.2.11"
    assert payload["entries"][0]["fingerprint"].startswith("SHA256:")


def test_fs_replace_can_render_pre_change_backup_command(monkeypatch):
    commands = []

    def fake_exec_remote(context, command, **kwargs):
        commands.append(command)
        return 0, "__AUTOMAX_CHANGED__\n1\n", ""

    monkeypatch.setattr(fs_extra, "exec_remote", fake_exec_remote)
    context = ExecutionContext(
        run_id="run-1",
        dry_run=False,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="host", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )

    result = fs_extra.FsReplacePlugin().execute(
        {
            "path": "/etc/app.conf",
            "pattern": "^port=.*$",
            "replacement": "port=8080",
            "backup": True,
            "backup_suffix": ".pre-automax",
        },
        context,
    )

    assert result.ok
    assert "shutil.copy2(path, backup_path)" in commands[0]
    assert "/etc/app.conf.pre-automax" not in commands[0]
    assert " .pre-automax " in commands[0]


def test_fs_replace_rejects_empty_backup_suffix():
    with pytest.raises(PluginValidationError, match="backup_suffix"):
        fs_extra.FsReplacePlugin().validate(
            {
                "path": "/etc/app.conf",
                "pattern": "x",
                "replacement": "y",
                "backup": True,
                "backup_suffix": "",
            }
        )



def test_archive_compress_and_decompress_render_stream_commands():
    from automax.plugins.archive import ArchiveCompressPlugin, ArchiveDecompressPlugin

    context = ExecutionContext(
        run_id="run-1",
        dry_run=False,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="host", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )

    compress = ArchiveCompressPlugin().manual_commands(
        {"source": "/tmp/app.log", "dest": "/tmp/app.log.gz"}, context
    )
    decompress = ArchiveDecompressPlugin().manual_commands(
        {"archive": "/tmp/app.log.bz2", "dest": "/tmp/app.log", "force": True}, context
    )

    assert "gzip -c /tmp/app.log > /tmp/app.log.gz" in compress[0]
    assert "bzip2 -dc /tmp/app.log.bz2 > /tmp/app.log" in decompress[0]


def test_archive_compress_rejects_unknown_auto_suffix():
    from automax.plugins.archive import ArchiveCompressPlugin

    with pytest.raises(PluginValidationError, match="compression auto"):
        ArchiveCompressPlugin().validate({"source": "/tmp/app.log", "dest": "/tmp/app.log.raw"})


def test_plan_diff_json_lists_unavailable_plugins_with_reason(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: diff-all-nodes
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: stat
            use: fs.stat
            with:
              path: /tmp/demo
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["plan", "--diff", "--job", str(job), "--inventory", str(inventory), "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["diffs"][0]["available"] is False
    assert payload["diffs"][0]["plugin"] == "fs.stat"
    assert "deterministic file diff" in payload["diffs"][0]["reason"]


def test_commands_render_json_includes_unavailable_reason(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: commands-reason
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: stat
            use: fs.stat
            with:
              path: /tmp/demo
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["commands", "render", "--job", str(job), "--inventory", str(inventory), "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["nodes"][0]["available"] is False
    assert "manual command" in payload["nodes"][0]["reason"]


def test_storage_and_linux_ops_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()
    for name in (
        "block.facts",
        "block.identity",
        "block.rescan",
        "block.partition_rescan",
        "block.partition",
        "block.wipe_signatures",
        "block.mkfs",
        "udev.rule",
        "udev.reload",
        "udev.trigger",
        "udev.settle",
        "multipath.status",
        "multipath.reload",
        "multipath.flush",
        "swap.present",
        "swap.absent",
        "limits.dropin",
        "pam.limits",
        "hosts.entry",
        "hostname.set",
        "resolver.config",
        "chrony.servers",
        "chrony.sources_assert",
        "env.set",
        "system.reboot",
        "download.file",
    ):
        assert name in names


def test_storage_manual_commands_cover_scsi_id_partprobe_and_backups():
    from automax.plugins.block import BlockIdentityPlugin, BlockPartitionPlugin, BlockWipeSignaturesPlugin

    context = ExecutionContext(
        run_id="test-run",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node1", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )

    assert "/usr/lib/udev/scsi_id -g -u -d /dev/sdb1" in BlockIdentityPlugin().manual_commands({"device": "/dev/sdb1"}, context)[0]
    partition = BlockPartitionPlugin().manual_commands(
        {
            "device": "/dev/sdb",
            "label": "gpt",
            "backup": True,
            "partitions": [{"number": 1, "name": "DATA01", "start": "1MiB", "end": "100%"}],
        },
        context,
    )[0]
    assert "sfdisk --dump" in partition
    assert "partprobe" in partition
    wipe = BlockWipeSignaturesPlugin().manual_commands({"device": "/dev/sdb1", "force": True}, context)
    assert "wipefs -n" in wipe[0]
    assert "wipefs -a" in wipe[-1]


def test_linux_ops_manual_commands_cover_resolver_env_download_and_sysctl():
    from automax.plugins.kernel import SysctlReloadPlugin
    from automax.plugins.linux_ops import DownloadFilePlugin, EnvSetPlugin, ResolverConfigPlugin

    context = ExecutionContext(
        run_id="test-run",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node1", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )

    resolver = ResolverConfigPlugin().manual_commands({"nameservers": ["192.0.2.53"]}, context)[0]
    assert "refusing to manage symlinked /etc/resolv.conf" in resolver
    env = EnvSetPlugin().manual_commands({"variables": {"APP_HOME": "/opt/app"}}, context)[0]
    assert env == "export APP_HOME=/opt/app"
    download = DownloadFilePlugin().manual_commands({"url": "https://example.invalid/file.rpm", "dest": "/tmp/file.rpm"}, context)
    assert "curl -fL" in download[0]
    assert "wget -O" in download[0]
    assert SysctlReloadPlugin().manual_commands({"file": "/etc/sysctl.conf", "sudo": True}, context) == ["sudo -n sysctl -p /etc/sysctl.conf"]


def test_linux_ops_diff_previews_cover_persistent_and_runtime_operations():
    from automax.plugins.block import BlockFactsPlugin
    from automax.plugins.fs_extra import FsReplacePlugin
    from automax.plugins.linux_ops import (
        DownloadFilePlugin,
        HostnameSetPlugin,
        PamLimitsPlugin,
        SwapAbsentPlugin,
        SwapPresentPlugin,
    )
    from automax.plugins.udev import UdevReloadPlugin

    context = ExecutionContext(
        run_id="test-run",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node1", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )

    swap_present = SwapPresentPlugin().diff_preview(
        {"path": "/swapfile", "persist": True, "opts": "defaults"}, context
    )[0]
    assert swap_present["kind"] == "fstab-plan"
    assert "+/swapfile none swap defaults 0 0" in swap_present["diff"]

    swap_absent = SwapAbsentPlugin().diff_preview({"path": "/swapfile", "persist": True}, context)[0]
    assert swap_absent["kind"] == "fstab-plan"
    assert "entries with first field /swapfile removed" in swap_absent["diff"]

    pam = PamLimitsPlugin().diff_preview({"files": ["/etc/pam.d/login"]}, context)[0]
    assert pam["kind"] == "pam-plan"
    assert "+session required pam_limits.so" in pam["diff"]

    hostname = HostnameSetPlugin().diff_preview({"name": "app01.example.com"}, context)[0]
    assert hostname["kind"] == "hostname-plan"
    assert "+app01.example.com" in hostname["diff"]

    download = DownloadFilePlugin().diff_preview(
        {"url": "https://example.invalid/app.rpm", "dest": "/tmp/app.rpm"}, context
    )[0]
    assert download["kind"] == "download-plan"
    assert "+url: https://example.invalid/app.rpm" in download["diff"]

    replace = FsReplacePlugin().diff_preview(
        {
            "path": "/etc/app.conf",
            "pattern": "^port=.*$",
            "replacement": "port=8080",
            "backup": True,
        },
        context,
    )[0]
    assert replace["kind"] == "replace-plan"
    assert "+pattern: ^port=.*$" in replace["diff"]
    assert "+backup_target: /etc/app.conf.bak" in replace["diff"]

    assert "read-only facts collector" in BlockFactsPlugin().diff_preview_reason({}, context)
    assert "runtime udev rules" in UdevReloadPlugin().diff_preview_reason({}, context)


def _sysops_preview_context() -> ExecutionContext:
    return ExecutionContext(
        run_id="test-run",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node1", host="127.0.0.1"),
        vars={},
        outputs={},
        secrets={},
    )


def test_lvm_plugins_render_manual_commands_and_previews():
    from automax.plugins.lvm import (
        LvmLvExtendPlugin,
        LvmLvPresentPlugin,
        LvmPvPresentPlugin,
        LvmResizeFsPlugin,
        LvmVgPresentPlugin,
    )

    names = AutomaxEngine().plugin_registry.names()
    for name in (
        "lvm.pv_present",
        "lvm.vg_present",
        "lvm.lv_present",
        "lvm.lv_extend",
        "lvm.resizefs",
    ):
        assert name in names

    context = _sysops_preview_context()
    assert "pvcreate" in LvmPvPresentPlugin().manual_commands({"device": "/dev/sdb"}, context)[0]
    assert "vgcreate" in " && ".join(LvmVgPresentPlugin().manual_commands({"name": "vg_app", "devices": ["/dev/sdb"]}, context))
    lv = LvmLvPresentPlugin().manual_commands({"vg": "vg_app", "name": "data", "size": "10G", "resizefs": True}, context)
    assert any("lvcreate" in command for command in lv)
    assert "lvextend -r" in LvmLvExtendPlugin().manual_commands({"vg": "vg_app", "name": "data", "size": "20G"}, context)[0]
    assert "resize2fs" in LvmResizeFsPlugin().manual_commands({"device": "/dev/vg_app/data", "fstype": "ext4"}, context)[0]
    assert LvmLvPresentPlugin().diff_preview({"vg": "vg_app", "name": "data", "size": "10G"}, context)[0]["kind"] == "lvm-plan"


def test_network_plugins_render_interface_route_bond_vlan_dns():
    from automax.plugins.network import (
        NetworkBondPlugin,
        NetworkDnsPlugin,
        NetworkInterfacePlugin,
        NetworkRoutePlugin,
        NetworkVlanPlugin,
    )

    names = AutomaxEngine().plugin_registry.names()
    for name in ("network.interface", "network.route", "network.bond", "network.vlan", "network.dns"):
        assert name in names

    context = _sysops_preview_context()
    assert "ip addr replace" in " && ".join(NetworkInterfacePlugin().manual_commands({"name": "eth0", "address": "192.0.2.10", "prefix": 24}, context))
    assert NetworkRoutePlugin().manual_commands({"dest": "default", "gateway": "192.0.2.1", "dev": "eth0"}, context)[0] == "sudo -n ip route replace default via 192.0.2.1 dev eth0"
    assert "modprobe bonding" in NetworkBondPlugin().manual_commands({"name": "bond0", "interfaces": ["eth1", "eth2"]}, context)[0]
    assert "type vlan id 100" in NetworkVlanPlugin().manual_commands({"name": "eth0.100", "parent": "eth0", "vlan_id": 100}, context)[0]
    assert "network-plan" == NetworkInterfacePlugin().diff_preview({"name": "eth0"}, context)[0]["kind"]
    assert NetworkDnsPlugin().manual_commands({"nameservers": ["192.0.2.53"]}, context)


def test_health_plugins_render_safe_assertions():
    from automax.plugins.health import HealthHttpPlugin, HealthListenPlugin, HealthPortPlugin, HealthProcessPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("health.port", "health.listen", "health.process", "health.http"):
        assert name in names

    context = _sysops_preview_context()
    assert "ss -H -ltn" in HealthPortPlugin().manual_commands({"port": 443}, context)[0]
    assert "ss -H -ltn" in HealthListenPlugin().manual_commands({"port": 8443}, context)[0]
    assert "pgrep -af" in HealthProcessPlugin().manual_commands({"pattern": "sshd"}, context)[0]
    assert "read-only process assertion" in HealthProcessPlugin().diff_preview_reason({"pattern": "sshd"}, context)
    assert HealthHttpPlugin().name == "health.http"


def test_pki_plugins_install_permissions_and_expiry_preview():
    from automax.plugins.pki import PkiCaInstallPlugin, PkiCertExpiryAssertPlugin, PkiKeyPermissionsPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("pki.ca_install", "pki.key_permissions", "pki.cert_expiry_assert"):
        assert name in names

    context = _sysops_preview_context()
    ca = PkiCaInstallPlugin().manual_commands({"dest": "/usr/local/share/ca-certificates/demo.crt", "content": "CERT"}, context)[0]
    assert "update-ca-certificates" in ca
    assert "cp -p" in ca
    assert "chmod 0600" in " && ".join(PkiKeyPermissionsPlugin().manual_commands({"path": "/etc/pki/private/key.pem", "mode": "0600"}, context))
    assert "openssl x509 -checkend" in PkiCertExpiryAssertPlugin().manual_commands({"path": "/etc/pki/cert.pem", "min_days": 10}, context)[0]
    assert PkiCaInstallPlugin().diff_preview({"dest": "/tmp/ca.crt", "content": "CERT"}, context)[0]["kind"] == "pki-plan"
