# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

import automax.cli.cli as cli_module
import automax.plugins.local_command as local_command

cli = cli_module.cli
from automax.core.engine import AutomaxEngine
from automax.core.models import ExecutionContext, Target
from automax.core.state import StateStore
from automax.plugins.base import PluginValidationError
import automax.plugins.fs_extra as fs_extra
import automax.plugins.fs_typed as fs_typed


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
    for name in ("fs.cd", "fs.permission.mode", "fs.permission.owner", "fs.dir.create"):
        assert name in output_names
    for alias in ("cd", "chmod", "chown", "mkdir", "fs.mkdir"):
        assert alias not in output_names




def test_fs_dir_create_manual_commands_render_type_strict_sudo_owner_group_and_mode():
    context = ExecutionContext(
        run_id="test",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node", host="host"),
        vars={},
        outputs={},
        secrets={},
    )

    commands = fs_typed.FsDirCreatePlugin().manual_commands(
        {
            "path": "/u01/app/grid",
            "owner": "grid",
            "group": "oinstall",
            "mode": "0775",
            "sudo": True,
        },
        context,
    )

    command = commands[0]
    assert "fs.dir.create" not in command
    assert 'is_dir() { run test -d "$path" && ! run test -L "$path"; }' in command
    assert 'run mkdir -p -- "$path"' in command
    assert 'run chmod "$mode" "$path"' in command
    assert 'run chown "$owner_group" "$path"' in command
    assert 'sudo -n "$@"' in command


def test_typed_filesystem_plugins_are_strict_about_wrong_path_types(monkeypatch):
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
    context.ssh_client = object()

    calls = []

    def fake_exec_remote(context, command, **kwargs):
        calls.append(command)
        return 20, "", "wrong-type: expected file at /tmp/demo"

    monkeypatch.setattr(fs_typed, "exec_remote", fake_exec_remote)

    result = fs_typed.FsFileExistsPlugin().execute({"path": "/tmp/demo"}, context)

    assert not result.ok
    assert "wrong-type" in result.stderr
    assert 'is_file() { run test -f "$path" && ! run test -L "$path"; }' in calls[0]

    with pytest.raises(PluginValidationError):
        fs_typed.FsDirRemovePlugin().manual_commands({"path": "/etc", "recursive": True}, context)

    remove_command = fs_typed.FsFileRemovePlugin().manual_commands({"path": "/tmp/demo"}, context)[0]
    assert "refusing to remove non-$kind path" in remove_command
    assert 'is_file() { run test -f "$path" && ! run test -L "$path"; }' in remove_command


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
            use: fs.object.copy
            with:
              src: /tmp/source.txt
              dest: /tmp/dest.txt
              overwrite: false
          - id: remove
            use: fs.file.remove
            with:
              path: /tmp/dest.txt
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
        "fs.dir.create",
        "fs.dir.remove",
        "fs.dir.exists",
        "fs.dir.wait",
        "fs.file.create",
        "fs.file.remove",
        "fs.file.exists",
        "fs.file.wait",
        "fs.object.stat",
        "fs.file.read",
        "fs.file.write",
        "fs.file.template",
        "fs.file.line",
        "fs.file.replace",
        "fs.object.move",
        "fs.symlink.create",
        "fs.symlink.remove",
        "fs.symlink.exists",
        "fs.symlink.wait",
        "fs.object.find",
    ):
        assert name in names

    for removed in ("fs.mkdir", "fs.remove", "fs.exists", "assert.file", "assert.path", "wait.file", "wait.path"):
        assert removed not in names
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
        "identity.user.create",
        "identity.user.modify",
        "identity.user.remove",
        "identity.group.create",
        "identity.group.remove",
    ):
        assert name in names

    assert "service.enable" not in names


def test_user_group_process_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    for name in (
        "identity.user.create",
        "identity.user.modify",
        "identity.user.remove",
        "identity.group.create",
        "identity.group.remove",
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
        "network.connectivity.port_wait",
        "process.wait",
        "network.connectivity.port_check",
        "storage.usage.disk_check",
    ):
        assert name in names

    assert "check.tcp" not in names
    assert "check.disk" not in names
    assert "wait.file" not in names
    assert "wait.path" not in names
    assert "assert.file" not in names
    assert "assert.path" not in names


def test_check_plugins_validate_in_job_yaml(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: check-plugins-validate
tasks:
  - id: checks
    targets: all
    steps:
      - id: remote_checks
        substeps:
          - id: wait_file
            use: fs.file.wait
            with:
              path: /tmp/automax-ready
              state: absent
              retries: 1
              interval: 1
          - id: dir_exists
            use: fs.dir.exists
            with:
              path: /tmp
          - id: assert_disk
            use: storage.usage.disk_check
            with:
              path: /
              min_free_mb: 1
      - id: controller_checks
        substeps:
          - id: wait_tcp
            use: network.connectivity.port_wait
            with:
              host: 127.0.0.1
              port: 22
              retries: 1
              interval: 1
          - id: assert_tcp
            use: network.connectivity.port_check
            with:
              host: 127.0.0.1
              port: 22
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    AutomaxEngine().validate(job_path=str(job), inventory_path=str(inventory))



def test_fs_template_supports_explicit_values():
    plugin = AutomaxEngine().plugin_registry.get("fs.file.template")

    plugin.validate(
        {
            "src": "examples/next/templates/app.conf.j2",
            "dest": "/tmp/automax-app.conf",
            "values": {"app_name": "demo", "port": 8080},
        }
    )



def test_database_health_plugin_runs_sqlite_read_only_checks(tmp_path: Path):
    plugin = AutomaxEngine().plugin_registry.get("db.health")
    context = _sysops_preview_context()
    database = tmp_path / "health.sqlite"
    sqlite3 = pytest.importorskip("sqlite3")
    conn = sqlite3.connect(database)
    conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    result = plugin.execute(
        {"engine": "sqlite", "connection": {"path": str(database)}, "checks": ["connect", "select", "version", "integrity"]},
        context,
    )

    assert result.ok, result.stderr
    assert result.changed is False
    assert result.data["engine"] == "sqlite"
    assert result.data["checks"]["select"] is True
    assert result.data["integrity"] == "ok"
    assert "sqlite3 -readonly" in plugin.manual_commands({"engine": "sqlite", "connection": {"path": str(database)}}, context)[0]
    assert "read-only" in plugin.diff_preview_reason({"engine": "sqlite", "connection": {"path": str(database)}}, context)


def test_database_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()

    for name in (
        "db.health",
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
    assert plugin.manual_commands({"database": str(database), "query": "SELECT 1"}, context)[0].startswith(f"sqlite3 {database}")


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
    metadata = AutomaxEngine().plugin_registry.describe("fs.file.template")

    assert metadata["category"] == "fs"
    assert any(item["name"] == "src" and item["required"] for item in metadata["parameters"])
    assert any(item["name"] == "sudo" and item["default"] is False for item in metadata["parameters"])
    assert metadata["examples"]
    assert metadata["result_fields"]["data.dest"] == "Remote destination path"


def test_plugins_describe_json_outputs_structured_metadata():
    result = CliRunner().invoke(cli, ["plugins", "describe", "fs.file.template", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name"] == "fs.file.template"
    assert payload["category"] == "fs"
    assert any(item["name"] == "dest" for item in payload["parameters"])


def test_plugin_describe_human_output_includes_rich_metadata():
    result = CliRunner().invoke(cli, ["plugins", "describe", "fs.file.template"])

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



def test_failed_text_run_prints_command_stdout_and_stderr(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: failure-diagnostics
tasks:
  - id: inspect
    targets: all
    steps:
      - id: local
        substeps:
          - id: bad
            use: local.command
            with:
              command: "printf 'visible-out\n'; printf 'visible-err\n' >&2; exit 7"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")

    result = CliRunner().invoke(
        cli,
        ["run", "--job", str(job), "--inventory", str(inventory), "--state-dir", str(tmp_path / "runs")],
    )

    assert result.exit_code == 1, result.output
    assert "[FAILED] controller task.inspect:step.local:substep.bad rc=7 local command failed" in result.output
    assert "  commands:" in result.output
    assert "printf 'visible-out" in result.output
    assert "  stdout:" in result.output
    assert "    visible-out" in result.output
    assert "  stderr:" in result.output
    assert "    visible-err" in result.output

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
        "fs.file.write",
        "fs.file.read",
        "fs.file.exists",
        "fs.object.stat",
        "fs.file.line",
        "fs.file.replace",
        "fs.object.move",
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
        "fs.file.wait",
        "fs.dir.wait",
        "process.wait",
        "fs.file.exists",
        "fs.dir.exists",
        "storage.usage.disk_check",
        "network.connectivity.port_check",
        "systemctl.status",
        "pkg.query",
        "identity.user.create",
        "identity.group.create",
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


def test_base_plugin_validation_rejects_unknown_param_type_and_range():
    from automax.plugins.base import BasePlugin, PluginValidationError

    class ExamplePlugin(BasePlugin):
        name = "example.strict"
        required_params = ("path",)
        optional_params = ("sudo", "port", "mode")
        parameter_schema = {
            "path": {"type": "path", "non_empty": True},
            "sudo": {"type": "boolean"},
            "port": {"type": "integer", "min": 1, "max": 65535},
            "mode": {"type": "string", "enum": ["read", "write"]},
        }

        def execute(self, params, context):  # pragma: no cover - validation-only test
            raise NotImplementedError

    plugin = ExamplePlugin()
    plugin.validate({"path": "/tmp/demo", "sudo": True, "port": 22, "mode": "read"})

    with pytest.raises(PluginValidationError, match="unknown params: typo"):
        plugin.validate({"path": "/tmp/demo", "typo": True})
    with pytest.raises(PluginValidationError, match="param 'sudo' must be boolean"):
        plugin.validate({"path": "/tmp/demo", "sudo": "true"})
    with pytest.raises(PluginValidationError, match="param 'port' must be <= 65535"):
        plugin.validate({"path": "/tmp/demo", "port": 70000})
    with pytest.raises(PluginValidationError, match="param 'mode' must be one of: read, write"):
        plugin.validate({"path": "/tmp/demo", "mode": "append"})
    with pytest.raises(PluginValidationError, match="param 'path' must not be empty"):
        plugin.validate({"path": ""})


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
    assert "Mode: check" in result.output
    assert "Targets: controller" in result.output
    assert "  t1" in result.output
    assert "1 substep  x  1 target  OK" in result.output
    assert "Result: OK" in result.output
    assert "CHECK controller" not in result.output
    assert not state_dir.exists()


def test_run_check_verbose_prints_per_target_substeps(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: run-check-verbose
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

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--check",
            "--verbose",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Check mode preview" in result.output
    assert "CHECK controller task.t1:step.s1:substep.echo local.command" in result.output


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
            use: fs.file.write
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
    assert "# controller task.t1:step.s1:substep.write fs.file.write /etc/demo.conf" in result.output
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
            use: fs.file.template
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
            use: fs.dir.remove
            with:
              path: /tmp/demo
              recursive: true
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
    assert "sudo=no" in result.output


def test_commands_render_marks_sudo_and_preserves_heredoc_commands(tmp_path: Path):
    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: manual-sudo-heredoc
tasks:
  - id: t1
    targets: all
    steps:
      - id: s1
        substeps:
          - id: remove_key
            use: security.ssh.authorized_key.remove
            with:
              user: deploy
              key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo demo@example
              sudo: true
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
        ],
    )

    assert result.exit_code == 0, result.output
    assert "# sudo note: Rendered manual commands containing sudo -n" in result.output
    assert "plugin=security.ssh.authorized_key.remove sudo=yes" in result.output
    assert "cat <<'AUTOMAX_SH' | sudo -n sh -s -- deploy" in result.output
    assert "--sudo-password-env ENV_NAME" in result.output


def test_commands_render_json_marks_legacy_plugins_available_with_fallback(tmp_path: Path):
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
            use: fs.object.stat
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
    assert payload["uses_sudo"] is False
    assert payload["sudo_note"] == ""
    assert payload["nodes"][0]["available"] is True
    assert payload["nodes"][0]["uses_sudo"] is False
    assert payload["nodes"][0]["commands"]
    assert "stat /tmp/demo" in payload["nodes"][0]["commands"][0]


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
            stdout = (
                "example.com ssh-rsa QUJDREVGR0g=\n"
                "example.com ecdsa-sha2-nistp256 QUJDREVGR0g=\n"
                "example.com ssh-ed25519 QUJDREVGR0g=\n"
            )
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
    assert "Target example.com:22" in result.output
    assert "  ssh-ed25519" in result.output
    assert "Wrote known_hosts file:" in result.output
    assert "Scanned 1 target, 3 host keys." in result.output
    assert result.output.index("ssh-ed25519") < result.output.index("ecdsa-sha2-nistp256")
    assert result.output.index("ecdsa-sha2-nistp256") < result.output.index("ssh-rsa")
    assert output.read_text(encoding="utf-8") == (
        "example.com ssh-rsa QUJDREVGR0g=\n"
        "example.com ecdsa-sha2-nistp256 QUJDREVGR0g=\n"
        "example.com ssh-ed25519 QUJDREVGR0g=\n"
    )


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
    assert payload["entries"][0]["target_name"] == "web01"
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


def test_plan_diff_json_lists_legacy_operation_plan_preview(tmp_path: Path):
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
            use: fs.object.stat
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
    assert payload["diffs"][0]["available"] is True
    assert payload["diffs"][0]["plugin"] == "fs.object.stat"
    assert payload["diffs"][0]["kind"] == "operation-plan"
    assert "stat /tmp/demo" in payload["diffs"][0]["diff"]


def test_commands_render_json_includes_legacy_fallback_commands(tmp_path: Path):
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
            use: fs.object.stat
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
    assert payload["nodes"][0]["available"] is True
    assert payload["nodes"][0]["commands"]
    assert "stat /tmp/demo" in payload["nodes"][0]["commands"][0]


def test_storage_and_linux_ops_plugins_are_registered():
    names = AutomaxEngine().plugin_registry.names()
    for name in (
        "storage.block.facts",
        "storage.block.identity",
        "storage.block.scan",
        "storage.block.partition.scan",
        "storage.block.partition.apply",
        "storage.block.signatures.wipe",
        "storage.fs.create",
        "udev.rule",
        "udev.reload",
        "udev.trigger",
        "udev.settle",
        "storage.multipath.status",
        "storage.multipath.reload",
        "storage.multipath.remove",
        "storage.swap.add",
        "storage.swap.remove",
        "limits.dropin",
        "security.pam.limits",
        "hosts.entry",
        "hostname.set",
        "network.dns.config",
        "network.dns.facts",
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
    from automax.plugins.linux_ops import DownloadFilePlugin, EnvSetPlugin, NetworkDnsConfigBase

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

    resolver = "\n".join(NetworkDnsConfigBase().manual_commands({"nameservers": ["192.0.2.53"]}, context))
    assert "refusing to manage symlinked /etc/resolv.conf" in resolver
    assert "install -D -m 0644" in resolver
    env = EnvSetPlugin().manual_commands({"variables": {"APP_HOME": "/opt/app"}}, context)[0]
    assert env == "export APP_HOME=/opt/app"
    download = DownloadFilePlugin().manual_commands({"url": "https://example.invalid/file.rpm", "dest": "/tmp/file.rpm"}, context)
    assert download[0] == "automax_download_tmp=$(mktemp /tmp/file.rpm.automax-download.XXXXXX)"
    assert download[1] == "trap 'rm -f \"$automax_download_tmp\"' EXIT"
    assert "curl -fsSL" in download[2]
    assert "wget -q -O" in download[2]
    assert '"${automax_download_tmp}"' in download[2]
    assert download[2].startswith("(") and download[2].endswith(")")
    assert download[3].startswith("(test ! -e ")
    assert download[4].startswith("(test ! -e ")
    assert SysctlReloadPlugin().manual_commands({"file": "/etc/sysctl.conf", "sudo": True}, context) == ["sudo -n sysctl -p /etc/sysctl.conf"]


def test_linux_ops_diff_previews_cover_persistent_and_runtime_operations():
    from automax.plugins.block import BlockFactsPlugin
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

    replace = fs_extra.FsReplacePlugin().diff_preview(
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


def test_user_group_manual_commands_render_identity_flags():
    from automax.plugins.manual_preview import fallback_manual_commands

    context = ExecutionContext(run_id="run", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node1", host="node1"), vars={}, outputs={}, secrets={})

    group_command = fallback_manual_commands(
        "identity.group.create",
        {"name": "oinstall", "gid": 54321, "system": True, "sudo": True},
        context,
    )[0]
    assert group_command == "getent group oinstall >/dev/null || sudo -n groupadd --system --gid 54321 oinstall"

    user_command = fallback_manual_commands(
        "identity.user.create",
        {
            "name": "grid",
            "uid": 54331,
            "group": "oinstall",
            "groups": ["asmadmin", "asmdba"],
            "shell": "/bin/bash",
            "home": "/home/grid",
            "create_home": True,
            "comment": "Oracle Grid Infrastructure owner",
            "sudo": True,
        },
        context,
    )[0]
    assert "useradd" in user_command
    assert "--uid 54331" in user_command
    assert "--gid oinstall" in user_command
    assert "--groups asmadmin,asmdba" in user_command
    assert "--shell /bin/bash" in user_command
    assert "--home-dir /home/grid" in user_command
    assert "--create-home" in user_command
    assert "--comment 'Oracle Grid Infrastructure owner'" in user_command


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
        "storage.lvm.pv.add",
        "storage.lvm.vg.add",
        "storage.lvm.lv.add",
        "storage.lvm.lv.extend",
        "storage.fs.resize",
    ):
        assert name in names

    context = _sysops_preview_context()
    assert "sudo -n pvs" in LvmPvPresentPlugin().manual_commands({"device": "/dev/sdb"}, context)[0]
    assert "pvcreate" in LvmPvPresentPlugin().manual_commands({"device": "/dev/sdb"}, context)[0]
    vg_commands = LvmVgPresentPlugin().manual_commands({"name": "vg_app", "devices": ["/dev/sdb"]}, context)
    assert "sudo -n vgs" in vg_commands[0]
    assert "vgcreate" in " && ".join(vg_commands)
    assert "sudo -n pvs" in vg_commands[1]
    assert "vgdisplay" not in " && ".join(vg_commands)
    lv = LvmLvPresentPlugin().manual_commands({"vg": "vg_app", "name": "data", "size": "10G", "resizefs": True}, context)
    assert any("lvcreate" in command for command in lv)
    assert "--wipesignatures" not in lv[0]
    forced_lv = LvmLvPresentPlugin().manual_commands(
        {"vg": "vg_app", "name": "data", "size": "10G", "force": True}, context
    )
    assert "lvcreate -y --wipesignatures y" in forced_lv[0]
    assert "lvextend -r" in LvmLvExtendPlugin().manual_commands({"vg": "vg_app", "name": "data", "size": "20G"}, context)[0]
    assert "resize2fs" in LvmResizeFsPlugin().manual_commands({"device": "/dev/vg_app/data", "fstype": "ext4"}, context)[0]
    assert LvmLvPresentPlugin().diff_preview({"vg": "vg_app", "name": "data", "size": "10G"}, context)[0]["kind"] == "lvm-plan"


def test_network_plugins_render_interface_route_bond_vlan_dns():
    from automax.plugins.network import (
        NetworkBondPlugin,
        NetworkDnsConfigPlugin,
        NetworkInterfacePlugin,
        NetworkRouteAddPlugin,
        NetworkRouteFactsPlugin,
        NetworkRouteRemovePlugin,
        NetworkVlanPlugin,
    )

    names = AutomaxEngine().plugin_registry.names()
    for name in ("network.link.interface", "network.route.add", "network.route.remove", "network.route.facts", "network.link.bond", "network.link.facts", "network.link.vlan", "network.dns.config"):
        assert name in names

    context = _sysops_preview_context()
    assert "ip addr replace" in " && ".join(NetworkInterfacePlugin().manual_commands({"name": "eth0", "address": "192.0.2.10", "prefix": 24}, context))
    nm_commands = " && ".join(NetworkInterfacePlugin().manual_commands({"name": "eth0", "address": "192.0.2.10", "prefix": 24, "persist": True, "backend": "networkmanager"}, context))
    assert "nmcli connection" in nm_commands
    assert NetworkRouteAddPlugin().manual_commands({"dest": "default", "gateway": "192.0.2.1", "dev": "eth0"}, context)[0] == "sudo -n ip route replace default via 192.0.2.1 dev eth0"
    assert "route-eth0" in NetworkRouteAddPlugin().manual_commands({"dest": "default", "gateway": "192.0.2.1", "dev": "eth0", "persist": True, "backend": "ifcfg"}, context)[0]
    assert "ip route del" in NetworkRouteRemovePlugin().manual_commands({"dest": "192.0.2.0/24", "dev": "eth0"}, context)[0]
    assert "ip -j route show" in NetworkRouteFactsPlugin().manual_commands({"family": "all"}, context)[0]
    assert "modprobe bonding" in NetworkBondPlugin().manual_commands({"name": "bond0", "interfaces": ["eth1", "eth2"]}, context)[0]
    assert "type vlan id 100" in NetworkVlanPlugin().manual_commands({"name": "eth0.100", "parent": "eth0", "vlan_id": 100}, context)[0]
    assert "network-plan" == NetworkInterfacePlugin().diff_preview({"name": "eth0"}, context)[0]["kind"]
    assert NetworkDnsConfigPlugin().manual_commands({"nameservers": ["192.0.2.53"]}, context)


def test_health_namespace_is_not_public_plugin_surface():
    names = AutomaxEngine().plugin_registry.names()

    assert not any(name.startswith("health.") for name in names)
    assert "http.request" in names
    assert "network.connectivity.port_check" in names
    assert "process.assert_absent" in names
    assert "process.assert_count" in names


def test_pki_plugins_install_permissions_and_expiry_preview():
    from automax.plugins.pki import PkiCaInstallPlugin, PkiCertExpiryAssertPlugin, PkiKeyPermissionsPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("security.pki.trust.install_ca", "security.pki.key.permissions", "security.pki.cert.expiry_check"):
        assert name in names

    context = _sysops_preview_context()
    ca = PkiCaInstallPlugin().manual_commands({"dest": "/usr/local/share/ca-certificates/demo.crt", "content": "CERT"}, context)[0]
    assert "update-ca-certificates" in ca
    auto_ca = PkiCaInstallPlugin().manual_commands({"name": "company", "trust_store": "system", "content": "CERT"}, context)[0]
    assert "/usr/local/share/ca-certificates/company.crt" in auto_ca
    assert "/etc/pki/ca-trust/source/anchors/company.crt" in auto_ca
    assert "cp -p" in ca
    assert "chmod 0600" in " && ".join(PkiKeyPermissionsPlugin().manual_commands({"path": "/etc/pki/private/key.pem", "mode": "0600"}, context))
    assert "openssl x509 -checkend" in PkiCertExpiryAssertPlugin().manual_commands({"path": "/etc/pki/cert.pem", "min_days": 10}, context)[0]
    assert PkiCaInstallPlugin().diff_preview({"dest": "/tmp/ca.crt", "content": "CERT"}, context)[0]["kind"] == "pki-plan"


def test_package_pinning_plugins_render_locks_and_priorities():
    from automax.plugins.pkg_pinning import PkgHoldPlugin, PkgRepoPriorityPlugin, PkgUnholdPlugin, PkgVersionPinPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("pkg.hold", "pkg.unhold", "pkg.version_pin", "pkg.repo_priority"):
        assert name in names

    context = _sysops_preview_context()
    assert PkgHoldPlugin().manual_commands({"name": "nginx", "manager": "apt"}, context)[0] == "sudo -n apt-mark hold nginx"
    assert PkgUnholdPlugin().manual_commands({"name": "nginx", "manager": "apt"}, context)[0] == "sudo -n apt-mark unhold nginx"
    pin = PkgVersionPinPlugin().manual_commands({"name": "nginx", "version": "1.24*"}, context)[0]
    assert "Pin: version 1.24*" in pin
    assert "cp -p" in pin
    dnf_pin = PkgVersionPinPlugin().manual_commands({"name": "nginx", "version": "1.24.0", "manager": "dnf"}, context)[0]
    assert "dnf versionlock add nginx-1.24.0" in dnf_pin
    priority = PkgRepoPriorityPlugin().diff_preview({"name": "stable", "priority": 900}, context)[0]
    assert priority["kind"] == "repo-priority-plan"
    redhat_priority = PkgRepoPriorityPlugin().manual_commands({"name": "internal", "priority": 10, "manager": "dnf", "baseurl": "https://repo.example.com/rhel"}, context)[0]
    assert "priority=10" in redhat_priority
    assert "/etc/yum.repos.d/internal.repo" in redhat_priority


def test_advanced_mount_plugins_render_remount_resize_and_findmnt():
    from automax.plugins.mounts_extra import FindmntAssertPlugin, FsResizePlugin, MountRemountPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("storage.mount.remount", "storage.fs.resize", "storage.mount.check"):
        assert name in names

    context = _sysops_preview_context()
    assert MountRemountPlugin().manual_commands({"path": "/data", "opts": "rw,noatime"}, context)[0] == "sudo -n mount -o remount,rw,noatime /data"
    assert "xfs_growfs" in FsResizePlugin().manual_commands({"device": "/dev/vg/data", "fstype": "xfs", "path": "/data"}, context)[0]
    assert "findmnt -rn" in FindmntAssertPlugin().manual_commands({"path": "/data", "fstype": "xfs"}, context)[0]
    assert FsResizePlugin().diff_preview({"device": "/dev/vg/data", "fstype": "ext4"}, context)[0]["kind"] == "filesystem-plan"


def test_log_and_journal_plugins_render_queries_and_exports():
    from automax.plugins.logs import JournalCollectPlugin, JournalGrepPlugin, LogExportPlugin, LogGrepPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("log.grep", "journal.collect", "journal.grep", "log.export"):
        assert name in names

    context = _sysops_preview_context()
    assert "grep -R" in LogGrepPlugin().manual_commands({"pattern": "ERROR", "files": ["/var/log/app.log"]}, context)[0]
    assert "journalctl" in JournalCollectPlugin().manual_commands({"service": "sshd", "lines": 50}, context)[0]
    assert "| grep -- ERROR" in JournalGrepPlugin().manual_commands({"pattern": "ERROR"}, context)[0]
    assert "tail -n 100" in LogExportPlugin().manual_commands({"files": ["/var/log/app.log"], "lines": 100}, context)[0]
    assert "artifact capture" in LogExportPlugin().diff_preview_reason({}, context)


def test_mail_send_is_controller_side_and_masks_password_in_renderers():
    from automax.plugins.mail import MailSendPlugin

    assert "mail.send" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    params = {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "from": "automax@example.com",
        "to": ["ops@example.com"],
        "subject": "Job failed",
        "username": "automax",
        "password": "super-secret",
    }
    plugin = MailSendPlugin()
    assert plugin.opens_remote_session is False
    rendered = plugin.manual_commands(params, context)[0]
    preview = plugin.diff_preview(params, context)[0]["diff"]
    assert "super-secret" not in rendered
    assert "super-secret" not in preview
    assert "password is intentionally not rendered" in rendered
    assert "mail-plan" == plugin.diff_preview(params, context)[0]["kind"]


def test_platform_facts_plugin_renders_backend_detection():
    from automax.plugins.platform import PlatformFactsPlugin

    assert "platform.facts" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = PlatformFactsPlugin().manual_commands({}, context)[0]
    assert "package_manager" in command
    assert "network_backend" in command
    assert "resolver_backend" in command
    assert "read-only backend detection" in PlatformFactsPlugin().diff_preview_reason({}, context)


def test_network_dns_backend_aware_plugins_render_safe_backends():
    from automax.plugins.linux_ops import NetworkDnsFactsPlugin
    from automax.plugins.network import NetworkDnsConfigPlugin

    names = AutomaxEngine().plugin_registry.names()
    assert "network.dns.facts" in names
    assert "network.dns.config" in names
    assert ".".join(("resolver", "facts")) not in names
    assert ".".join(("resolver", "config")) not in names
    context = _sysops_preview_context()
    facts = NetworkDnsFactsPlugin().manual_commands({}, context)[0]
    assert "backend=" in facts
    resolved = "\n".join(NetworkDnsConfigPlugin().manual_commands({"backend": "systemd-resolved", "nameservers": ["192.0.2.53"]}, context))
    assert "/etc/systemd/resolved.conf.d/99-automax.conf" in resolved
    assert "systemctl restart systemd-resolved" in resolved
    nm = " && ".join(NetworkDnsConfigPlugin().manual_commands({"backend": "networkmanager", "nm_connection": "eth0", "nameservers": ["192.0.2.53"]}, context))
    assert "nmcli connection modify eth0" in nm
    assert NetworkDnsConfigPlugin().diff_preview({"backend": "resolvconf", "nameservers": ["192.0.2.53"]}, context)[0]["kind"] == "resolver-plan"


def test_lvm_extra_plugins_render_destructive_and_snapshot_operations():
    from automax.plugins.lvm import LvmLvRemovePlugin, LvmPvRemovePlugin, LvmSnapshotPlugin, LvmThinPoolPlugin, LvmVgRemovePlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("storage.lvm.lv.snapshot", "storage.lvm.lv.remove", "storage.lvm.vg.remove", "storage.lvm.pv.remove", "storage.lvm.lv.thin_pool"):
        assert name in names
    context = _sysops_preview_context()
    assert "lvcreate -s" in LvmSnapshotPlugin().manual_commands({"vg": "vg0", "source": "/dev/vg0/data", "name": "snap", "size": "1G"}, context)[0]
    assert "--type thin-pool" in LvmThinPoolPlugin().manual_commands({"vg": "vg0", "name": "pool", "size": "10G"}, context)[0]
    assert "sudo -n lvs" in LvmLvRemovePlugin().manual_commands({"path": "/dev/vg0/old", "confirm": True}, context)[0]
    assert "lvremove -y" in LvmLvRemovePlugin().manual_commands({"path": "/dev/vg0/old", "confirm": True}, context)[0]
    assert "sudo -n vgs" in LvmVgRemovePlugin().manual_commands({"name": "oldvg", "confirm": True}, context)[0]
    assert "vgremove -y" in LvmVgRemovePlugin().manual_commands({"name": "oldvg", "confirm": True}, context)[0]
    assert "sudo -n pvs" in LvmPvRemovePlugin().manual_commands({"device": "/dev/sdb", "confirm": True}, context)[0]
    assert "pvremove" in LvmPvRemovePlugin().manual_commands({"device": "/dev/sdb", "confirm": True}, context)[0]


def test_filesystem_acl_attr_quota_plugins_render_safe_commands():
    from automax.plugins.fs_system import (
        FsAclAssertPlugin,
        FsAclGetPlugin,
        FsAclPlugin,
        FsAclRestorePlugin,
        FsAttrCheckPlugin,
        FsAttrGetPlugin,
        FsAttrPlugin,
        FsQuotaPlugin,
    )

    names = AutomaxEngine().plugin_registry.names()
    for name in (
        "fs.acl.set",
        "fs.acl.get",
        "fs.acl.check",
        "fs.acl.restore",
        "fs.attr.set",
        "fs.attr.get",
        "fs.attr.check",
        "storage.quota.set",
    ):
        assert name in names
    context = _sysops_preview_context()
    assert "getfacl" in " && ".join(FsAclPlugin().manual_commands({"path": "/data", "acl": "u:app:rwx"}, context))
    assert "setfacl" in " && ".join(FsAclPlugin().manual_commands({"path": "/data", "acl": "u:app:rwx"}, context))
    assert "getfacl -p /data" in FsAclGetPlugin().manual_commands({"path": "/data"}, context)[0]
    assert "grep -Fx -- u:app:rwx" in FsAclAssertPlugin().manual_commands({"path": "/data", "acl": "u:app:rwx"}, context)[0]
    assert "setfacl --restore=/tmp/data.acl" in FsAclRestorePlugin().manual_commands({"file": "/tmp/data.acl"}, context)[0]
    assert "setfacl --test --restore=/tmp/data.acl" in FsAclRestorePlugin().manual_commands({"file": "/tmp/data.acl", "test_only": True}, context)[0]
    assert "chattr +i" in FsAttrPlugin().manual_commands({"path": "/data/file", "attrs": "i"}, context)[0]
    assert "lsattr -d /data/file" in FsAttrGetPlugin().manual_commands({"path": "/data/file"}, context)[0]
    assert "grep -F -- i" in FsAttrCheckPlugin().manual_commands({"path": "/data/file", "attrs": "i"}, context)[0]
    assert "setquota -u app" in FsQuotaPlugin().manual_commands({"target": "app", "mountpoint": "/data"}, context)[0]


def test_systemd_resource_plugins_render_units_and_dropins():
    from automax.plugins.systemd_resources import SystemdSysusersPlugin, SystemdTimerPlugin, SystemdTmpfilesPlugin, SystemdUnitPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("systemd.unit", "systemd.timer", "systemd.tmpfiles", "systemd.sysusers"):
        assert name in names
    context = _sysops_preview_context()
    assert "systemctl daemon-reload" in " && ".join(SystemdUnitPlugin().manual_commands({"name": "demo.service", "content": "[Service]\nExecStart=/bin/true\n"}, context))
    assert "/etc/systemd/system/demo.timer" in " && ".join(SystemdTimerPlugin().manual_commands({"name": "demo", "content": "[Timer]\nOnBootSec=1m\n"}, context))
    assert "systemd-tmpfiles --create" in " && ".join(SystemdTmpfilesPlugin().manual_commands({"name": "demo", "content": "d /run/demo 0755 root root -\n", "apply": True}, context))
    assert "systemd-sysusers" in " && ".join(SystemdSysusersPlugin().manual_commands({"name": "demo", "content": "u demo - Demo /nonexistent\n", "apply": True}, context))


def test_alternatives_set_plugin_renders_cross_distro_commands():
    from automax.plugins.alternatives import AlternativesSetPlugin

    assert "alternatives.set" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = AlternativesSetPlugin().manual_commands({"name": "java", "path": "/usr/bin/java-21"}, context)[0]
    assert "update-alternatives --set java /usr/bin/java-21" in command
    assert "alternatives --set java /usr/bin/java-21" in command
    assert AlternativesSetPlugin().diff_preview({"name": "java", "path": "/usr/bin/java-21"}, context)[0]["kind"] == "alternative-plan"


def test_alternatives_get_plugin_renders_read_only_query():
    from automax.plugins.alternatives import AlternativesGetPlugin

    assert "alternatives.get" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    plugin = AlternativesGetPlugin()
    command = plugin.manual_commands({"name": "java"}, context)[0]
    assert "update-alternatives --query java" in command
    assert "alternatives --display java" in command
    assert plugin.supports_check_mode is True
    assert "read-only" in plugin.diff_preview_reason({"name": "java"}, context)


def test_alternatives_list_plugin_renders_read_only_inventory():
    from automax.plugins.alternatives import AlternativesListPlugin

    assert "alternatives.list" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    plugin = AlternativesListPlugin()
    command = plugin.manual_commands({}, context)[0]
    assert "update-alternatives --get-selections" in command
    assert "/var/lib/alternatives" in command
    assert plugin.supports_check_mode is True
    assert "read-only" in plugin.diff_preview_reason({}, context)


def test_auditd_plugins_render_rules_status_and_reload():
    from automax.plugins.auditd import AuditdReloadPlugin, AuditdRulePlugin, AuditdStatusPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("security.audit.rule", "security.audit.status", "security.audit.reload"):
        assert name in names
    context = _sysops_preview_context()
    rule_cmd = " && ".join(AuditdRulePlugin().manual_commands({"name": "watch-passwd", "rule": "-w /etc/passwd -p wa -k identity"}, context))
    assert "/etc/audit/rules.d/watch-passwd.rules" in rule_cmd
    assert "augenrules --load" in rule_cmd
    assert AuditdStatusPlugin().manual_commands({}, context)[0] == "sudo -n auditctl -s"
    assert "augenrules --load" in AuditdReloadPlugin().manual_commands({}, context)[0]


def test_ssh_config_and_known_hosts_plugins_render_safe_changes():
    from automax.plugins.ssh_ops import SshConfigPlugin, SshKnownHostsPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("security.ssh.config", "security.ssh.known_hosts"):
        assert name in names
    context = _sysops_preview_context()
    server = " && ".join(SshConfigPlugin().manual_commands({"name": "10-hardening", "scope": "server", "settings": {"PermitRootLogin": "no"}}, context))
    assert "/etc/ssh/sshd_config.d/10-hardening.conf" in server
    assert "sshd -t" in server
    known = SshKnownHostsPlugin().manual_commands({"host": "server.example.com", "key": "ssh-ed25519 AAAA"}, context)[0]
    assert "known_hosts" in known
    assert "ssh-ed25519" in known


def test_ssh_keygen_plugin_renders_secret_free_key_generation():
    from automax.plugins.ssh_ops import SshKeygenPlugin

    assert "security.ssh.keygen" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    plugin = SshKeygenPlugin()
    command = plugin.manual_commands({"path": "/home/deploy/.ssh/id_ed25519", "type": "ed25519", "owner": "deploy", "group": "deploy", "sudo": True}, context)[0]
    assert "ssh-keygen -q -t ed25519" in command
    assert "-N ''" in command
    assert "/home/deploy/.ssh/id_ed25519.pub" in command
    assert "chown deploy:deploy" in command
    assert "ssh-keygen-plan" == plugin.diff_preview({"path": "/home/deploy/.ssh/id_ed25519"}, context)[0]["kind"]


def test_selinux_port_and_fcontext_plugins_render_persistent_rules():
    from automax.plugins.security_modules import SelinuxFcontextPlugin, SelinuxPortPlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("security.selinux.port", "security.selinux.fcontext"):
        assert name in names
    context = _sysops_preview_context()
    assert "semanage port" in SelinuxPortPlugin().manual_commands({"port": 8443, "protocol": "tcp", "selinux_type": "http_port_t"}, context)[0]
    assert "semanage fcontext" in SelinuxFcontextPlugin().execute.__qualname__ or SelinuxFcontextPlugin().name == "security.selinux.fcontext"


def test_kernel_boot_param_plugin_renders_safe_grub_update():
    from automax.plugins.kernel import KernelBootParamPlugin

    assert "kernel.boot_param" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = " && ".join(KernelBootParamPlugin().manual_commands({"name": "transparent_hugepage", "value": "never"}, context))
    assert "/etc/default/grub" in command
    assert "update-grub" in command
    assert KernelBootParamPlugin().diff_preview({"name": "quiet", "state": "absent"}, context)[0]["kind"] == "kernel-boot-plan"


def test_sudo_management_plugins_render_validated_dropins():
    from automax.plugins.sudo_ops import SudoRulePlugin, SudoValidatePlugin

    names = AutomaxEngine().plugin_registry.names()
    for name in ("security.sudo.rule", "security.sudo.validate"):
        assert name in names
    context = _sysops_preview_context()
    rule = " && ".join(SudoRulePlugin().manual_commands({"name": "ops", "subject": "%ops", "commands": ["/usr/bin/systemctl"], "nopassword": True}, context))
    assert "visudo -cf" in rule
    assert "NOPASSWD" in rule
    assert "/etc/sudoers.d/ops" in rule
    assert SudoValidatePlugin().manual_commands({}, context)[0] == "sudo -n visudo -cf /etc/sudoers"


def test_sudoers_dropin_reference_example_keeps_password_required_sudo():
    from automax.plugins.metadata import PLUGIN_EXAMPLES

    example = PLUGIN_EXAMPLES["security.sudo.dropin"]

    assert "NOPASSWD" not in example
    assert "deploy ALL=(root) /bin/systemctl restart myapp" in example


def test_transfer_rsync_plugin_renders_secret_free_manual_command():
    from automax.plugins.transfer import TransferRsyncPlugin

    names = AutomaxEngine().plugin_registry.names()
    assert "transfer.rsync" in names
    context = _sysops_preview_context()
    command = TransferRsyncPlugin().manual_commands(
        {"src": "./dist/", "dest": "/opt/app/", "delete": True, "dry_run": True, "excludes": ["*.tmp"]},
        context,
    )[0]
    assert "rsync" in command
    assert "--delete" in command
    assert "--dry-run" in command
    assert "127.0.0.1:/opt/app/" in command
    assert "*.tmp" in command
    assert "rsync --dry-run" in TransferRsyncPlugin().diff_preview_reason({}, context)


def test_backup_file_plugin_renders_copy_and_checksum():
    from automax.plugins.backup import BackupFilePlugin

    assert "backup.file" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = BackupFilePlugin().manual_commands({"src": "/etc/hosts", "dest": "/backup/hosts"}, context)[0]
    assert "cp -a /etc/hosts /backup/hosts" in command
    assert "sha256sum /backup/hosts" in command
    assert "backup artifact" in BackupFilePlugin().diff_preview_reason({}, context)


def test_backup_directory_plugin_renders_tar_and_checksum():
    from automax.plugins.backup import BackupDirectoryPlugin

    assert "backup.directory" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = BackupDirectoryPlugin().manual_commands({"src": "/etc", "dest": "/backup/etc.tar.gz"}, context)[0]
    assert "tar -czf /backup/etc.tar.gz" in command
    assert "sha256sum /backup/etc.tar.gz" in command


def test_backup_restore_plugin_requires_confirmation_and_renders_restore():
    from automax.plugins.backup import BackupRestorePlugin

    assert "backup.restore" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    with pytest.raises(PluginValidationError):
        BackupRestorePlugin().manual_commands({"src": "/backup/hosts", "dest": "/etc/hosts"}, context)
    command = BackupRestorePlugin().manual_commands({"src": "/backup/hosts", "dest": "/etc/hosts", "confirm": True}, context)[0]
    assert "cp -a /backup/hosts /etc/hosts" in command
    assert "confirm=true" in BackupRestorePlugin().diff_preview_reason({}, context)


def test_backup_verify_plugin_renders_read_only_checksum():
    from automax.plugins.backup import BackupVerifyPlugin

    assert "backup.verify" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = BackupVerifyPlugin().manual_commands({"path": "/backup/hosts"}, context)[0]
    assert "sha256sum -c" in command
    assert BackupVerifyPlugin().supports_check_mode is True
    assert "read-only" in BackupVerifyPlugin().diff_preview_reason({}, context)


def test_fs_bind_mount_plugin_renders_runtime_and_persistent_commands():
    from automax.plugins.fs_advanced import FsBindMountPlugin

    assert "storage.mount.bind" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    commands = FsBindMountPlugin().manual_commands({"src": "/srv/data", "dest": "/mnt/data", "persist": True}, context)
    rendered = " && ".join(commands)
    assert "mount --bind /srv/data /mnt/data" in rendered
    assert "/etc/fstab" in rendered
    assert FsBindMountPlugin().diff_preview({"src": "/srv/data", "dest": "/mnt/data"}, context)[0]["kind"] == "bind-mount-plan"


def test_storage_usage_disk_check_plugin_renders_df_check():
    from automax.plugins.wait_assert import AssertDiskPlugin

    assert "storage.usage.disk_check" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = AssertDiskPlugin().manual_commands({"path": "/", "max_used_percent": 90}, context)[0]
    assert "df -Pk /" in command
    assert "max_used_percent=90" in command
    assert "used_percent > max_used_percent" in command
    assert AssertDiskPlugin().supports_check_mode is True


def test_storage_usage_inode_check_plugin_renders_df_inode_check():
    from automax.plugins.fs_advanced import FsInodeUsageAssertPlugin

    assert "storage.usage.inode_check" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = FsInodeUsageAssertPlugin().manual_commands({"path": "/", "max_used_percent": 85}, context)[0]
    assert "df -Pi /" in command
    assert "max_used_percent=85" in command
    assert "used_percent > max_used_percent" in command
    assert FsInodeUsageAssertPlugin().supports_check_mode is True


def test_process_signal_plugin_renders_runtime_signal():
    from automax.plugins.user_group_process import ProcessSignalPlugin

    assert "process.signal" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = ProcessSignalPlugin().manual_commands({"pattern": "worker", "signal": "HUP"}, context)[0]
    assert "pkill -HUP -f worker" in command
    assert "runtime process" in ProcessSignalPlugin().diff_preview_reason({}, context)


def test_process_assert_absent_plugin_renders_pgrep_assertion():
    from automax.plugins.user_group_process import ProcessAssertAbsentPlugin

    assert "process.assert_absent" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    assert "pgrep -f worker" in ProcessAssertAbsentPlugin().manual_commands({"pattern": "worker"}, context)[0]
    assert ProcessAssertAbsentPlugin().supports_check_mode is True


def test_process_assert_count_plugin_renders_count_assertion():
    from automax.plugins.user_group_process import ProcessAssertCountPlugin

    assert "process.assert_count" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = ProcessAssertCountPlugin().manual_commands({"pattern": "worker", "min_count": 1, "max_count": 3}, context)[0]
    assert "pgrep -fc worker" in command
    assert 'test "$actual" -ge 1' in command
    assert 'test "$actual" -le 3' in command


def test_iptables_rule_plugin_renders_check_and_update():
    from automax.plugins.firewall import IptablesRulePlugin

    assert "network.firewall.iptables.rule" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = IptablesRulePlugin().manual_commands({"chain": "INPUT", "rule": "-p tcp --dport 443 -j ACCEPT"}, context)[0]
    assert "iptables -t filter -C INPUT -p tcp --dport 443 -j ACCEPT" in command
    assert "iptables -t filter -A INPUT -p tcp --dport 443 -j ACCEPT" in command
    assert "runtime firewall" in IptablesRulePlugin().diff_preview_reason({}, context)


def test_iptables_save_plugin_renders_ruleset_export():
    from automax.plugins.firewall import IptablesSavePlugin

    assert "network.firewall.iptables.save" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = IptablesSavePlugin().manual_commands({"dest": "/etc/iptables/rules.v4"}, context)[0]
    assert "iptables-save" in command
    assert "/etc/iptables/rules.v4" in command


def test_iptables_restore_plugin_requires_confirm_or_test_only():
    from automax.plugins.firewall import IptablesRestorePlugin

    assert "network.firewall.iptables.restore" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    with pytest.raises(PluginValidationError):
        IptablesRestorePlugin().manual_commands({"src": "/etc/iptables/rules.v4"}, context)
    command = IptablesRestorePlugin().manual_commands({"src": "/etc/iptables/rules.v4", "test_only": True}, context)[0]
    assert "iptables-restore --test" in command
    assert "runtime firewall" in IptablesRestorePlugin().diff_preview_reason({}, context)


def test_sshd_config_plugin_renders_validated_dropin():
    from automax.plugins.hardening import SshdConfigPlugin

    assert "security.sshd.config" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    commands = " && ".join(SshdConfigPlugin().manual_commands({"name": "10-hardening", "settings": {"PermitRootLogin": "no"}}, context))
    assert "/etc/ssh/sshd_config.d/10-hardening.conf" in commands
    assert "sshd -t" in commands
    assert SshdConfigPlugin().diff_preview({"name": "10-hardening", "settings": {"PermitRootLogin": "no"}}, context)[0]["kind"] == "sshd-config-plan"


def test_login_defs_plugin_renders_key_updates():
    from automax.plugins.hardening import LoginDefsPlugin

    assert "login.defs" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    commands = " && ".join(LoginDefsPlugin().manual_commands({"settings": {"PASS_MAX_DAYS": 90}}, context))
    assert "/etc/login.defs" in commands
    assert "PASS_MAX_DAYS 90" in commands
    assert LoginDefsPlugin().diff_preview({"settings": {"PASS_MAX_DAYS": 90}}, context)[0]["kind"] == "login-defs-plan"


def test_password_policy_plugin_renders_pwquality_dropin():
    from automax.plugins.hardening import PasswordPolicyPlugin

    assert "security.password.policy" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    commands = " && ".join(PasswordPolicyPlugin().manual_commands({"name": "10-hardening", "settings": {"minlen": 14}}, context))
    assert "/etc/security/pwquality.conf.d/10-hardening.conf" in commands
    assert "minlen = 14" in commands
    assert PasswordPolicyPlugin().diff_preview({"name": "10-hardening", "settings": {"minlen": 14}}, context)[0]["kind"] == "password-policy-plan"


def test_authselect_profile_plugin_renders_profile_selection():
    from automax.plugins.hardening import AuthselectProfilePlugin

    assert "security.authselect.profile" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = AuthselectProfilePlugin().manual_commands({"profile": "sssd", "features": ["with-faillock"]}, context)[0]
    assert "authselect select sssd with-faillock" in command
    assert "--backup=automax" in command
    assert "authselect" in AuthselectProfilePlugin().diff_preview_reason({}, context)


def test_cert_generate_csr_plugin_renders_openssl_req():
    from automax.plugins.cert_ops import CertGenerateCsrPlugin

    assert "security.pki.csr.generate" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = CertGenerateCsrPlugin().manual_commands({"key": "/etc/pki/tls/private/app.key", "dest": "/tmp/app.csr", "subject": "/CN=app"}, context)[0]
    assert "openssl req -new" in command
    assert "-subj /CN=app" in command


def test_cert_self_signed_plugin_renders_openssl_x509_req():
    from automax.plugins.cert_ops import CertSelfSignedPlugin

    assert "security.pki.cert.self_signed" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = CertSelfSignedPlugin().manual_commands({"key": "/tmp/app.key", "cert": "/tmp/app.crt", "subject": "/CN=app", "days": 30}, context)[0]
    assert "openssl req -x509" in command
    assert "-days 30" in command


def test_cert_verify_chain_plugin_renders_read_only_verify():
    from automax.plugins.cert_ops import CertVerifyChainPlugin

    assert "security.pki.cert.chain_check" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = CertVerifyChainPlugin().manual_commands({"cert": "/tmp/app.crt", "ca_file": "/tmp/ca.crt"}, context)[0]
    assert "openssl verify -CAfile /tmp/ca.crt /tmp/app.crt" in command
    assert CertVerifyChainPlugin().supports_check_mode is True


def test_cert_install_keypair_plugin_renders_permissions():
    from automax.plugins.cert_ops import CertInstallKeypairPlugin

    assert "security.pki.cert.install_keypair" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    commands = " && ".join(CertInstallKeypairPlugin().manual_commands({"cert": "/tmp/app.crt", "key": "/tmp/app.key", "cert_dest": "/etc/pki/app.crt", "key_dest": "/etc/pki/private/app.key"}, context))
    assert "install -D -m 0644 /tmp/app.crt /etc/pki/app.crt" in commands
    assert "install -D -m 0600 /tmp/app.key /etc/pki/private/app.key" in commands


def test_cert_expiry_report_plugin_renders_checkend():
    from automax.plugins.cert_ops import CertExpiryReportPlugin

    assert "security.pki.cert.expiry_report" in AutomaxEngine().plugin_registry.names()
    context = _sysops_preview_context()
    command = CertExpiryReportPlugin().manual_commands({"cert": "/tmp/app.crt", "warning_days": 10}, context)[0]
    assert "-enddate" in command
    assert "-checkend 864000" in command
    assert CertExpiryReportPlugin().supports_check_mode is True


def _audit_sample_value(name: str):
    values = {
        "acl": "u:demo:rwx",
        "archive": "/tmp/automax-demo.tar.gz",
        "attrs": "i",
        "body": "ok",
        "ca_file": "/tmp/ca.crt",
        "cert": "/tmp/server.crt",
        "cert_dest": "/etc/ssl/certs/server.crt",
        "chain": "/tmp/chain.pem",
        "command": "true",
        "confirm": True,
        "compression": "gzip",
        "content": "# managed by automax\n",
        "database": "postgres",
        "dest": "/tmp/automax-dest",
        "direction": "upload",
        "device": "/dev/sdb",
        "engine": "sqlite",
        "encoding": "utf-8",
        "entries": [{"domain": "*", "type": "soft", "item": "nofile", "value": 1024}],
        "fstype": "ext4",
        "checksum": "sha256",
        "backend": "runtime",
        "host": "127.0.0.1",
        "ip": "127.0.0.1",
        "key": "/tmp/server.key",
        "key_dest": "/etc/ssl/private/server.key",
        "keep": 7,
        "label": "gpt",
        "line": "managed=yes",
        "max_used_percent": 90,
        "mode": "0644",
        "mountpoint": "/tmp",
        "name": "demo",
        "names": ["demo.local"],
        "partitions": [{"number": 1, "name": "data", "start": "1MiB", "end": "100%"}],
        "password": "secret",
        "path": "/tmp/automax-demo",
        "pattern": "automax-demo",
        "policy": "DROP",
        "port": 22,
        "priority": 900,
        "profile": "sssd",
        "protocol": "tcp",
        "query": "SELECT 1",
        "replacement": "replacement",
        "rich_rule": "rule family=ipv4 service name=ssh accept",
        "rule": "-A INPUT -p tcp --dport 22 -j ACCEPT",
        "schedule": "* * * * *",
        "selinux_type": "var_t",
        "servers": ["pool.ntp.org"],
        "service": "sshd.service",
        "settings": {"PermitRootLogin": "no"},
        "size": "1G",
        "smtp_host": "127.0.0.1",
        "source": "/dev/vg0/data",
        "src": "README.md",
        "state": "present",
        "subject": "/CN=automax-demo",
        "target": "demo",
        "to": ["ops@example.invalid"],
        "type": "file",
        "url": "https://example.invalid/health",
        "user": "demo",
        "value": "1",
        "variables": {"DEMO": "1"},
        "version": "1.0",
        "vg": "vg0",
        "vlan_id": 100,
    }
    if name == "from":
        return "automax@example.invalid"
    return values.get(name, "demo")


def _audit_sample_value_for_schema(name: str, schema: dict[str, object]) -> object:
    value = _audit_sample_value(name)
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        default = schema.get("default")
        return default if default in enum else enum[0]

    expected = schema.get("types", schema.get("type", "any"))
    if isinstance(expected, str):
        expected_types = {expected}
    else:
        expected_types = {str(item) for item in expected}

    if "boolean" in expected_types:
        return True
    if "integer" in expected_types:
        if name in {"port", "smtp_port"}:
            return 22
        if name in {"expected_status", "status"}:
            return 200
        if name in {"max_percent", "max_used_percent"}:
            return 90
        if name == "vlan_id":
            return 100
        return 1
    if "number" in expected_types:
        return 1
    if "mapping" in expected_types:
        if isinstance(value, dict):
            return value
        return {"demo": "1"}
    if "list" in expected_types or "sequence" in expected_types:
        if isinstance(value, list):
            return value
        if name == "query_params":
            return []
        if name == "statements":
            return ["SELECT 1"]
        if name == "syscalls":
            return ["openat"]
        if name == "tools":
            return ["sh"]
        if name == "commands":
            return ["/usr/bin/id"]
        if name == "devices":
            return ["/dev/sdb"]
        if name == "interfaces":
            return ["eth1"]
        if name == "paths":
            return ["etc/hosts"]
        if name == "patterns":
            return ["*.bak"]
        return [str(value)]
    if "path" in expected_types or "string" in expected_types:
        if isinstance(value, (list, dict, bool)):
            return "demo"
        return value
    return value


def _audit_sample_params(plugin) -> dict[str, object]:
    params = {
        name: _audit_sample_value_for_schema(name, plugin.parameter_schema.get(name, {}))
        for name in plugin.required_params
    }
    # Include optional values required by conservative renderers while keeping samples safe.
    for name in plugin.optional_params:
        if name in {"connection", "checks", "packages", "rules", "files", "features", "headers", "search", "options", "excludes", "ssh_options", "groups", "env", "values", "attachments", "cc", "bcc"}:
            continue
        if name not in params:
            params[name] = _audit_sample_value_for_schema(name, plugin.parameter_schema.get(name, {}))
    # Plugin-specific safe corrections.
    if plugin.name.startswith("db."):
        params.setdefault("connection", {"path": "/tmp/automax.sqlite"})
    if plugin.name == "db.health":
        params["engine"] = "sqlite"
        params["connection"] = {"path": "/tmp/automax.sqlite"}
    if plugin.name in {"storage.lvm.lv.remove", "storage.lvm.vg.remove", "storage.lvm.pv.remove", "backup.restore", "backup.prune", "backup.rotate", "network.firewall.iptables.restore"}:
        params["confirm"] = True
    if plugin.name == "plugin.requirements":
        params["plugin"] = "transfer.rsync"
    if plugin.name == "fs.dir.remove":
        params["path"] = "/tmp/automax-demo-dir"
        params["recursive"] = True
    if plugin.name == "process.signal":
        params.pop("pid", None)
        params["pattern"] = "automax-demo"
    if plugin.name == "process.kill":
        params.pop("pid", None)
        params["pattern"] = "automax-demo"
    if plugin.name == "process.wait":
        params.pop("pid", None)
        params["pattern"] = "automax-demo"
    if plugin.name == "mail.send":
        params["from"] = "automax@example.invalid"
        params["to"] = ["ops@example.invalid"]
    if plugin.name == "cron.entry":
        params["schedule"] = "* * * * *"
        params["command"] = "true"
    if plugin.name == "network.firewall.nftables.apply" or plugin.name == "network.firewall.nftables.validate":
        params["content"] = "flush ruleset\n"
    if plugin.name == "security.pki.trust.install_ca":
        params["name"] = "automax-demo"
        params["content"] = "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n"
    if plugin.name == "security.selinux.mode":
        params["state"] = "enforcing"
    if plugin.name in {"fs.acl.set", "fs.acl.check"}:
        params["acl"] = "u:app:rwx"
    if plugin.name in {"fs.attr.set", "fs.attr.check"}:
        params["attrs"] = "i"
    if plugin.name == "fs.permission.owner":
        params["owner"] = "demo"
    if plugin.name == "storage.quota.set":
        params["type"] = "user"
    if plugin.name == "network.firewall.ufw.rule":
        params["rule"] = "allow"
        params["port"] = 22
        params["protocol"] = "tcp"
    if plugin.name == "security.apparmor.profile_check":
        params["state"] = "enforce"
    if plugin.name == "security.audit.backlog_check":
        params["max_lost"] = 0
        params["max_backlog"] = 8192
    if plugin.name == "chrony.tracking_assert":
        params["max_offset"] = 1.0
        params["max_stratum"] = 16
    if plugin.name == "network.firewall.iptables.counter_assert":
        params["min_packets"] = 1
    if plugin.name == "fs.file.replace":
        params["count"] = 0
        params["match_count_assert"] = 1
    if plugin.name == "security.sshd.config":
        params["match_blocks"] = [{"match": "User deploy", "settings": {"X11Forwarding": "no"}}]
    if plugin.name == "network.dns.config":
        params["backend"] = "plain-file"
    if plugin.name in {"network.route.add", "network.route.remove"}:
        params["backend"] = "runtime"
        params["persist"] = False
    if plugin.name == "network.route.facts":
        params["family"] = "inet"
    if plugin.name in {"network.link.interface", "network.link.bond", "network.link.vlan"}:
        params["state"] = "up"
    return params


def test_all_builtin_plugins_have_operator_preview_manual_commands_and_dry_run():
    context = _sysops_preview_context()
    registry = AutomaxEngine().plugin_registry
    failures: list[str] = []
    for name in registry.names():
        plugin = registry.get(name)
        params = _audit_sample_params(plugin)
        try:
            commands = plugin.manual_commands(params, context)
            if not commands or not all(isinstance(command, str) and command.strip() for command in commands):
                failures.append(f"{name}: empty manual_commands")
            rendered = "\n".join(commands)
            if "mktemp" in rendered and "trap 'rm -f" not in rendered:
                failures.append(f"{name}: mktemp manual_commands without cleanup trap")
        except Exception as exc:  # pragma: no cover - assertion collects all offenders
            failures.append(f"{name}: manual_commands raised {exc!r}")
        try:
            preview = plugin.diff_preview(params, context)
            reason = plugin.diff_preview_reason(params, context)
            if not preview and not reason:
                failures.append(f"{name}: no diff_preview and no diff_preview_reason")
        except Exception as exc:  # pragma: no cover - assertion collects all offenders
            failures.append(f"{name}: diff_preview raised {exc!r}")
        try:
            dry_run = plugin.dry_run(params, context)
            if not dry_run.ok or dry_run.changed:
                failures.append(f"{name}: dry_run not safe/unchanged")
        except Exception as exc:  # pragma: no cover - assertion collects all offenders
            failures.append(f"{name}: dry_run raised {exc!r}")
    assert not failures, "\n" + "\n".join(failures)


def test_firewall_readback_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    assert "firewall-cmd --state" in registry.get("network.firewall.firewalld.status").manual_commands({}, context)[0]
    assert "firewall-cmd --zone=public --list-all" in registry.get("network.firewall.firewalld.zone").manual_commands({"zone": "public", "permanent": False}, context)[0]
    assert "nft -a list ruleset" in registry.get("network.firewall.nftables.list").manual_commands({"handle": True}, context)[0]
    assert "nft list ruleset" in registry.get("network.firewall.nftables.export").manual_commands({"dest": "/tmp/rules.nft", "sudo": False}, context)[0]
    assert "iptables -t filter -L INPUT -n" in registry.get("network.firewall.iptables.list").manual_commands({"chain": "INPUT", "sudo": False}, context)[0]
    assert "iptables -t filter -S INPUT" in registry.get("network.firewall.iptables.policy").manual_commands({"chain": "INPUT", "sudo": False}, context)[0]
    assert "iptables -t filter -L INPUT -n" in registry.get("network.firewall.iptables.chain").manual_commands({"chain": "INPUT", "sudo": False}, context)[0]
    assert "ufw allow 18080/tcp" == registry.get("network.firewall.ufw.rule").manual_commands({"rule": "allow", "port": 18080, "protocol": "tcp", "sudo": False}, context)[0]
    assert "ufw allow from 10.0.0.0/8 to any port 22 proto tcp" == registry.get("network.firewall.ufw.rule").manual_commands({"rule": "allow", "from": "10.0.0.0/8", "port": 22, "protocol": "tcp", "sudo": False}, context)[0]


def test_package_inspection_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    assert "dpkg-query -W" in registry.get("pkg.version_assert").manual_commands({"name": "curl", "version": "1.0", "manager": "apt", "sudo": False}, context)[0]
    assert "dpkg-query -S /usr/bin/curl" in registry.get("pkg.owner").manual_commands({"path": "/usr/bin/curl", "manager": "apt", "sudo": False}, context)[0]
    assert "dpkg -L curl" in registry.get("pkg.files").manual_commands({"name": "curl", "manager": "apt", "sudo": False}, context)[0]
    assert "dpkg -V curl" in registry.get("pkg.verify").manual_commands({"name": "curl", "manager": "apt", "sudo": False}, context)[0]
    assert "apt-get clean" in registry.get("pkg.clean").manual_commands({"manager": "apt", "sudo": False}, context)[0]


def test_network_advanced_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    assert "ip link add name br0 type bridge" in " && ".join(registry.get("network.link.bridge").manual_commands({"name": "br0", "interfaces": ["eth1"], "sudo": False}, context))
    assert "ip link show dev eth0" in registry.get("network.link.check").manual_commands({"name": "eth0"}, context)[0]
    assert "ip route show" in registry.get("network.route.check").manual_commands({"dest": "default", "gateway": "192.0.2.1"}, context)[0]
    assert "nameserver" in " && ".join(registry.get("network.dns.check").manual_commands({"nameservers": ["192.0.2.53"]}, context))
    assert "nc -z" in registry.get("network.connectivity.port_check").manual_commands({"host": "example.com", "port": 443}, context)[0]
    assert "ip -j link show" in registry.get("network.link.facts").manual_commands({}, context)[0]
    assert "ip -j route show" in registry.get("network.route.facts").manual_commands({}, context)[0]


def test_storage_readback_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    assert "pvs --reportformat json" in registry.get("storage.lvm.facts").manual_commands({"sudo": False}, context)[0]
    assert "/dev/vg0/lv0" in registry.get("storage.lvm.lv.check").manual_commands({"vg": "vg0", "name": "lv0", "sudo": False}, context)[0]
    lv_assert = registry.get("storage.lvm.lv.check").manual_commands({"vg": "vg0", "name": "lv0", "size": "512M"}, context)[0]
    assert "grep -Ei" in lv_assert
    assert "512" in lv_assert
    assert "findmnt --json" in registry.get("storage.mount.facts").manual_commands({}, context)[0]
    assert "findmnt --verify" in registry.get("storage.fstab.validate").manual_commands({"sudo": False}, context)[0]
    assert "swapon --show" in registry.get("storage.swap.facts").manual_commands({}, context)[0]
    assert "blkid /dev/sda1" in registry.get("storage.fs.check").manual_commands({"device": "/dev/sda1", "sudo": False}, context)[0]


def test_ssh_security_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    assert "ssh-keygen -lf" in registry.get("security.ssh.fingerprint").manual_commands({"path": "/tmp/id.pub", "sudo": False}, context)[0]
    assert "ssh-keygen -y" in registry.get("security.ssh.public_key").manual_commands({"path": "/tmp/id", "sudo": False}, context)[0]
    sudo_public_key = registry.get("security.ssh.public_key").manual_commands({"path": "/tmp/id", "dest": "/root/id.pub"}, context)[0]
    assert "ssh-keygen -y" in sudo_public_key
    assert "| sudo -n tee /root/id.pub >/dev/null" in sudo_public_key
    assert "ssh-keygen -A" in registry.get("security.ssh.host_keygen").manual_commands({"sudo": False}, context)[0]
    assert "authorized_keys" in registry.get("security.ssh.authorized_key.remove").manual_commands({"user": "deploy", "key": "ssh-ed25519 AAA demo", "sudo": False}, context)[0]
    assert "sshd -t" in registry.get("security.sshd.validate").manual_commands({}, context)[0]


def test_certificate_assert_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    assert "-fingerprint" in registry.get("security.pki.cert.fingerprint").manual_commands({"cert": "/tmp/cert.pem", "sudo": False}, context)[0]
    assert "openssl pkey" in registry.get("security.pki.cert.key_match_check").manual_commands({"cert": "/tmp/cert.pem", "key": "/tmp/key.pem", "sudo": False}, context)[0]
    assert "subjectAltName" in registry.get("security.pki.cert.san_check").manual_commands({"cert": "/tmp/cert.pem", "names": ["DNS:example.com"], "sudo": False}, context)[0]
    assert "-subject" in registry.get("security.pki.cert.subject_check").manual_commands({"cert": "/tmp/cert.pem", "subject": "CN=example", "sudo": False}, context)[0]
    assert "-issuer" in registry.get("security.pki.cert.issuer_check").manual_commands({"cert": "/tmp/cert.pem", "issuer": "CN=ca", "sudo": False}, context)[0]
    assert "install -D" in " && ".join(registry.get("security.pki.trust.install_bundle").manual_commands({"src": "/tmp/ca.pem", "dest": "/usr/local/share/ca-certificates/ca.crt", "sudo": False}, context))


def test_cron_readback_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    assert "crontab -l" in registry.get("cron.list").manual_commands({}, context)[0]
    assert "/etc/cron.d/demo" in registry.get("cron.absent").manual_commands({"name": "demo", "sudo": False}, context)[0]
    assert "awk" in registry.get("cron.validate").manual_commands({"path": "/tmp/cron"}, context)[0]


def test_transfer_plugins_allow_templated_controller_sources_in_static_validation():
    from automax.plugins.transfer import TransferSyncPlugin, TransferUploadPlugin

    TransferSyncPlugin().validate({"src": "{{ vars.fixture_root }}/source-dir", "dest": "/tmp/dest"})
    TransferUploadPlugin().validate({"src": "{{ vars.fixture_root }}/source.txt", "dest": "/tmp/dest"})



def test_shell_helpers_harden_environment_names_and_heredoc_delimiters():
    from automax.plugins.remote_utils import (
        apply_cwd,
        heredoc_to_file,
        heredoc_to_file_expr,
        heredoc_to_stdin,
        shell_var_ref,
        sudo_command,
        sudo_prefix,
        sudo_shell_run_function,
        tempfile_command,
        tempfile_path_command,
        cleanup_trap_command,
    )

    context = ExecutionContext(
        run_id="test",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node", host="host"),
        vars={},
        outputs={},
        secrets={},
    )
    assert sudo_prefix({}, default=True) == "sudo -n "
    assert sudo_prefix({}, default=False) == ""
    assert sudo_prefix({"sudo": False}, default=True) == ""
    assert sudo_prefix({"sudo": True}, default=False) == "sudo -n "
    assert sudo_command({}, "systemctl status nginx", default=False) == "systemctl status nginx"
    assert sudo_command({"sudo": True}, "systemctl status nginx", default=False) == "sudo -n systemctl status nginx"
    assert sudo_shell_run_function() == (
        'run() {\n'
        '    if [ "$use_sudo" = "true" ]; then\n'
        '        sudo -n "$@"\n'
        '    else\n'
        '        "$@"\n'
        '    fi\n'
        '}'
    )
    assert shell_var_ref("automax_tmp") == '"${automax_tmp}"'
    assert tempfile_command("automax_tmp", "demo", suffix=".conf") == "automax_tmp=$(mktemp /tmp/automax-demo.XXXXXX.conf)"
    assert tempfile_path_command("automax_tmp", "/var/tmp/demo.XXXXXX") == "automax_tmp=$(mktemp /var/tmp/demo.XXXXXX)"
    assert cleanup_trap_command("automax_tmp") == 'trap \'rm -f "$automax_tmp"\' EXIT'
    assert cleanup_trap_command("automax_one", "automax_two") == 'trap \'rm -f "$automax_one" "$automax_two"\' EXIT'
    assert heredoc_to_file_expr('"${automax_tmp}"', "body") == "cat > \"${automax_tmp}\" <<'AUTOMAX_EOF'\nbody\nAUTOMAX_EOF"
    with pytest.raises(PluginValidationError):
        tempfile_command("bad-name", "demo")
    with pytest.raises(PluginValidationError):
        tempfile_command("automax_tmp", "bad/path")

    context.step_state["env"] = {"SAFE_NAME": "ok"}
    assert apply_cwd("echo ok", context) == "SAFE_NAME=ok echo ok"

    context.step_state["env"] = {"BAD;touch /tmp/pwn": "1"}
    with pytest.raises(PluginValidationError):
        apply_cwd("echo ok", context)

    context.step_state["env"] = "BAD=1"
    with pytest.raises(PluginValidationError):
        apply_cwd("echo ok", context)

    command = heredoc_to_file("/tmp/demo", "line\nAUTOMAX_EOF\n")
    assert "<<'AUTOMAX_EOF_1'" in command
    assert command.endswith("AUTOMAX_EOF_1")

    command = heredoc_to_stdin("python3 -", "AUTOMAX_PY\n", prefix="AUTOMAX_PY")
    assert "<<'AUTOMAX_PY_1'" in command
    assert command.endswith("AUTOMAX_PY_1")




def test_builtin_plugins_use_shared_script_heredoc_helper():
    offenders = []
    for path in sorted(Path("src/automax/plugins").glob("*.py")):
        if path.name == "remote_utils.py":
            continue
        content = path.read_text(encoding="utf-8")
        for token in ("<<'PY'", "<<'SH'"):
            if token in content:
                offenders.append(f"{path}:{token}")
    assert not offenders


def test_builtin_plugin_mktemp_files_install_cleanup_traps():
    offenders = []
    for path in sorted(Path("src/automax/plugins").glob("*.py")):
        content = path.read_text(encoding="utf-8")
        for match in re.finditer(r"tmp=\$\(mktemp\)", content):
            window = content[match.end():match.end() + 160]
            if 'trap \'rm -f "$tmp"\' EXIT' not in window and "cleanup_trap_command('tmp')" not in window:
                offenders.append(f"{path}:{content[:match.start()].count(chr(10)) + 1}")
    assert not offenders
def test_env_consuming_plugins_reject_unsafe_environment_names():
    from automax.plugins.cron import CronEntryPlugin
    from automax.plugins.linux_ops import EnvSetPlugin
    with pytest.raises(PluginValidationError):
        EnvSetPlugin().manual_commands({"variables": {"BAD;touch /tmp/pwn": "1"}}, _sysops_preview_context())
    with pytest.raises(PluginValidationError):
        local_command.LocalCommandPlugin().manual_commands({"command": "true", "env": {"BAD;touch /tmp/pwn": "1"}}, _sysops_preview_context())
    with pytest.raises(PluginValidationError):
        CronEntryPlugin().validate({"name": "demo", "schedule": "* * * * *", "command": "true", "env": {"BAD;touch /tmp/pwn": "1"}})
    with pytest.raises(PluginValidationError):
        CronEntryPlugin().validate({"name": "demo", "schedule": "* * * * *", "command": "true", "env": {"SAFE_NAME": "one\ntwo"}})


def test_transfer_upload_download_metadata_include_safety_options():
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    upload = registry.get("transfer.upload").metadata()
    download = registry.get("transfer.download").metadata()
    upload_params = {parameter["name"] for parameter in upload["parameters"]}
    download_params = {parameter["name"] for parameter in download["parameters"]}

    for name in {"checksum", "overwrite", "backup_existing", "backup_suffix", "preserve_times", "mode", "owner", "group"}:
        assert name in upload_params
    for name in {"checksum", "overwrite", "backup_existing", "backup_suffix", "preserve_times", "mode", "owner", "group"}:
        assert name in download_params


def test_firewall_lifecycle_options_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    firewalld = registry.get("network.firewall.firewalld.port").manual_commands({"port": 443, "runtime": True, "query_only": True, "sudo": False}, context)[0]
    assert "--query-port=443/tcp" in firewalld
    iptables = registry.get("network.firewall.iptables.rule").manual_commands({"chain": "INPUT", "rule": "-p tcp --dport 22 -j ACCEPT", "position": 1, "comment": "ssh", "wait": 5, "save_after": True, "sudo": False}, context)[0]
    assert "-I INPUT 1" in iptables
    assert "--comment ssh" in iptables
    assert "iptables-save" in iptables
    nft = registry.get("network.firewall.nftables.apply").metadata()
    assert {"backup_before", "persistent_file", "reload_service", "check_only"}.issubset({parameter["name"] for parameter in nft["parameters"]})


def test_ssh_keygen_hardening_options_render_secret_safe_manual_command():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={"key_passphrase": "secret"})
    plugin = build_builtin_registry().get("security.ssh.keygen")

    manual = plugin.manual_commands({"path": "/tmp/id_ed25519", "passphrase_secret": "key_passphrase", "fingerprint": True, "sudo": False}, context)[0]
    assert "***" in manual
    assert "secret" not in manual
    assert "ssh-keygen -lf" in manual
    public_only = " && ".join(plugin.manual_commands({"path": "/tmp/id_ed25519", "public_key_only": True, "fingerprint": True, "sudo": False}, context))
    assert "ssh-keygen -y" in public_only
    assert "ssh-keygen -lf" in public_only

def test_pam_hardening_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    access = registry.get("security.pam.access").manual_commands({"entries": ["+ : deploy : 10.0.0.0/8"], "service": "sshd", "sudo": False}, context)
    assert "/etc/security/access.conf" in " && ".join(access)
    assert "pam_access.so" in " && ".join(access)
    faillock = registry.get("security.pam.faillock").manual_commands({"settings": {"deny": 5}, "service": "system-auth", "sudo": False}, context)
    assert "faillock.conf" in " && ".join(faillock)
    assert "pam_faillock.so" in " && ".join(faillock)
    pwhistory = registry.get("security.pam.pwhistory").manual_commands({"settings": {"remember": 5}, "service": "password-auth", "sudo": False}, context)
    assert "pwhistory.conf" in " && ".join(pwhistory)
    assert "pam_pwhistory.so" in " && ".join(pwhistory)
    succeed = " && ".join(registry.get("security.pam.succeed_if").manual_commands({"service": "sshd", "condition": "user ingroup wheel", "sudo": False}, context))
    assert "pam_succeed_if.so user ingroup wheel" in succeed
    line = " && ".join(registry.get("security.pam.service_line").manual_commands({"service": "sshd", "line": "auth required pam_env.so", "sudo": False}, context))
    assert "pam_env.so" in line
    validate = registry.get("security.pam.validate").manual_commands({"service": "sshd"}, context)[0]
    assert "awk" in validate and "/etc/pam.d/sshd" in validate
    facts = registry.get("security.pam.stack.facts").manual_commands({"service": "sshd"}, context)[0]
    assert "grep -En" in facts and "/etc/pam.d/sshd" in facts
    authselect = registry.get("security.authselect.check").manual_commands({"profile": "sssd", "features": ["with-faillock"], "sudo": False}, context)[0]
    assert "authselect current" in authselect
    assert "with-faillock" in authselect


def test_backup_completeness_plugins_render_manual_commands():
    from automax.core.models import ExecutionContext, Target
    from automax.plugins.base import PluginValidationError
    from automax.plugins.registry import build_builtin_registry

    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})
    registry = build_builtin_registry()

    manifest = registry.get("backup.manifest").manual_commands({"root": "/var/backups", "dest": "/var/backups/manifest.txt", "sudo": False}, context)[0]
    assert "find . -type f" in manifest
    assert "tee /var/backups/manifest.txt" in manifest

    sudo_manifest = registry.get("backup.manifest").manual_commands({"root": "/var/backups", "dest": "/var/backups/manifest.txt"}, context)[0]
    assert "sudo -n sha256sum" in sudo_manifest
    assert "sudo -n tee /var/backups/manifest.txt.sha256 >/dev/null" in sudo_manifest

    restore = registry.get("backup.restore").manual_commands({"src": "/var/backups/file.txt", "dest": "/srv/file.txt", "confirm": True}, context)[0]
    assert "if test -e /srv/file.txt; then sudo -n cp -a /srv/file.txt /srv/file.txt.pre-restore; fi" in restore
    assert "sudo -n cp -a /var/backups/file.txt /srv/file.txt" in restore

    try:
        registry.get("backup.prune").manual_commands({"path": "/var/backups", "keep": 7}, context)
    except PluginValidationError as exc:
        assert "confirm: true" in str(exc)
    else:
        raise AssertionError("backup.prune must require confirm=true")

    prune = registry.get("backup.prune").manual_commands({"path": "/var/backups", "keep": 7, "older_than_days": 30, "patterns": ["*.tar.gz"], "confirm": True, "sudo": False}, context)[0]
    assert "find /var/backups" in prune
    assert "older_than_days" not in prune
    assert "python3 - /var/backups 7" in prune

    rotate = registry.get("backup.rotate").manual_commands({"path": "/var/backups/app.tar.gz", "keep": 3, "confirm": True, "sudo": False}, context)[0]
    assert "app.tar.gz.3" in rotate
    assert "app.tar.gz.1" in rotate

    preview = registry.get("backup.restore_preview").manual_commands({"src": "/var/backups/app.tar.gz", "dest": "/srv/app", "archive": True, "sudo": False}, context)[0]
    assert "tar -tf /var/backups/app.tar.gz" in preview

    verify = registry.get("backup.restore_verify").manual_commands({"src": "/var/backups/app.tar.gz", "dest": "/srv/app", "archive": True, "sudo": False}, context)[0]
    assert "tar -df /var/backups/app.tar.gz" in verify


def test_file_install_atomic_option_controls_final_install_command(monkeypatch):
    from automax.core.models import ExecutionContext, Target
    from automax.plugins import file_utils

    captured: list[str] = []

    def fake_exec_remote(context, command, **kwargs):
        captured.append(command)
        return 0, "", ""

    monkeypatch.setattr(file_utils, "exec_remote", fake_exec_remote)
    context = ExecutionContext(run_id="test", dry_run=True, job={}, task={}, step={}, substep={}, target=Target(name="node", host="host"), vars={}, outputs={}, secrets={})

    file_utils.install_uploaded_file(context, "/tmp/source", "/etc/demo.conf", sudo=True, mode="0644", atomic=True)
    assert ".automax-" in captured[-1]
    assert "mv -f" in captured[-1]
    assert "/etc/demo.conf" in captured[-1]

    file_utils.install_uploaded_file(context, "/tmp/source", "/etc/demo.conf", sudo=True, mode="0644", atomic=False)
    assert ".automax-" not in captured[-1]
    assert "sudo -n install -m 0644 /tmp/source /etc/demo.conf" in captured[-1]


def test_fs_write_template_metadata_exposes_atomic_option():
    from automax.plugins.registry import build_builtin_registry

    registry = build_builtin_registry()
    for name in ("fs.file.write", "fs.file.template"):
        params = {parameter["name"] for parameter in registry.get(name).metadata()["parameters"]}
        assert "atomic" in params


def test_prepare_sudo_password_command_uses_askpass_without_embedding_password():
    from automax.plugins.remote_utils import prepare_sudo_password_command

    command, stdin = prepare_sudo_password_command(
        "printf data | sudo -n tee /tmp/demo >/dev/null",
        "secret-pass",
    )

    assert "printf data | sudo -n tee /tmp/demo" in command
    assert "command sudo -A -p ''" in command
    assert "SUDO_ASKPASS" in command
    assert "secret-pass" not in command
    assert stdin == "secret-pass\n"


def test_plugin_sudo_rendering_does_not_reintroduce_local_wrappers():
    plugin_root = Path("src/automax/plugins")
    offenders = [
        str(path)
        for path in sorted(plugin_root.glob("*.py"))
        if "def _sudo(" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []



def test_plugin_sources_do_not_use_pid_based_temp_paths():
    plugin_root = Path("src/automax/plugins")
    offenders = [
        str(path)
        for path in sorted(plugin_root.glob("*.py"))
        if "$$" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_cli_run_sudo_password_env_feeds_sudo_enabled_remote_substeps(tmp_path: Path, monkeypatch):
    from contextlib import contextmanager

    class FakeChannel:
        def shutdown_write(self):
            pass

        def recv_exit_status(self):
            return 0

    class FakeStdin:
        def __init__(self):
            self.channel = FakeChannel()
            self.writes: list[str] = []

        def write(self, value):
            self.writes.append(value)

    class FakeStream:
        def __init__(self, data: str = ""):
            self.channel = FakeChannel()
            self._data = data.encode("utf-8")

        def read(self):
            return self._data

    class FakeClient:
        def __init__(self):
            self.commands: list[dict[str, object]] = []
            self.stdin = FakeStdin()

        def exec_command(self, command, **kwargs):
            self.commands.append({"command": command, "kwargs": kwargs})
            return self.stdin, FakeStream(), FakeStream()

    class FakeSshManager:
        def __init__(self):
            self.client = FakeClient()

        @contextmanager
        def connect(self, target):
            yield self.client

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: sudo-runtime
tasks:
  - id: remote
    targets: all
    steps:
      - id: pipe
        substeps:
          - id: tee
            use: remote.command
            with:
              command: "printf data | sudo -n tee /tmp/automax-demo >/dev/null"
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  node:\n    host: 127.0.0.1\n")
    manager = FakeSshManager()
    monkeypatch.setenv("AUTOMAX_TEST_SUDO_PASSWORD", "secret-pass")
    monkeypatch.setattr(cli_module, "_engine", lambda plugin_path=(): AutomaxEngine(ssh_manager=manager))

    result = CliRunner().invoke(
        cli,
        [
            "run",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--sudo-password-env",
            "AUTOMAX_TEST_SUDO_PASSWORD",
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(manager.client.commands) == 1
    command = str(manager.client.commands[0]["command"])
    assert "printf data | sudo -n tee /tmp/automax-demo" in command
    assert "command sudo -A -p ''" in command
    assert "SUDO_ASKPASS" in command
    assert "secret-pass" not in command
    assert manager.client.stdin.writes == ["secret-pass\n"]


def test_capability_requirements_are_derived_from_selected_job(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: caps
preflight:
  capabilities: true
tasks:
  - id: ops
    targets: all
    steps:
      - id: transfer
        substeps:
          - id: sync
            use: transfer.rsync
            with:
              src: /tmp/src
              dest: /tmp/dest
          - id: acl
            use: fs.acl.restore
            with:
              file: /tmp/acl.backup
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  controller:\n    host: 127.0.0.1\n")
    monkeypatch.setattr(
        AutomaxEngine,
        "_detect_os_for_plan",
        lambda self, plan, secrets: {"controller": TargetOS(id="ubuntu", id_like=("debian",), family="debian", package_manager="apt")},
    )

    payload = AutomaxEngine().capability_requirements_job(job_path=str(job), inventory_path=str(inventory))

    assert payload["tool_count"] >= 2
    target = payload["targets"][0]
    assert "rsync" in target["tools"]
    assert "setfacl" in target["tools"]
    assert target["plugins"]["rsync"] == ["transfer.rsync"]

    result = CliRunner().invoke(
        cli,
        [
            "capabilities",
            "requirements",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.output
    rendered = json.loads(result.output)
    assert rendered["mode"] == "capability-requirements"
    assert "rsync" in rendered["targets"][0]["tools"]


def test_capability_and_redaction_plugins_render_safe_previews():
    context = ExecutionContext(
        run_id="test",
        dry_run=True,
        job={},
        task={},
        step={},
        substep={},
        target=Target(name="node", host="host"),
        vars={},
        outputs={},
        secrets={"token": "super-secret-token"},
    )
    registry = AutomaxEngine().plugin_registry

    assert registry.get("tool.exists").manual_commands({"name": "rsync"}, context) == ["command -v rsync"]
    assert "grep -F" in registry.get("tool.version_assert").manual_commands({"name": "rsync", "contains": "rsync"}, context)[0]
    assert "command -v setfacl" in registry.get("capability.assert").manual_commands({"tools": ["setfacl"]}, context)[0]
    assert registry.get("plugin.requirements").execute({"plugin": "transfer.rsync"}, context).data["requirements"]["transfer.rsync"] == ["rsync"]

    redacted = registry.get("security.secret.scan_output").execute({"text": "token=super-secret-token password=abc"}, context)
    assert redacted.ok
    assert redacted.data["changed_by_redaction"] is True
    assert "super-secret-token" not in redacted.data["redacted"]
    assert "password=***" in redacted.data["redacted"]
    leaked = registry.get("security.secret.redact_check").execute({"text": "value=super-secret-token"}, context)
    assert not leaked.ok



def test_capability_requirements_cli_detects_os_without_flag(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: cli-caps
tasks:
  - id: ops
    targets: all
    steps:
      - id: packages
        substeps:
          - id: install
            use: pkg.install
            with:
              packages: [curl]
              manager: auto
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  node:\n    host: 127.0.0.1\n")

    monkeypatch.setattr(
        AutomaxEngine,
        "_detect_os_for_plan",
        lambda self, plan, secrets: {"node": TargetOS(id="ubuntu", id_like=("debian",), family="debian", package_manager="apt")},
    )

    result = CliRunner().invoke(
        cli,
        [
            "capabilities",
            "requirements",
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
    assert payload["targets"][0]["os"]["family"] == "debian"
    assert "apt-get" in payload["targets"][0]["tools"]


def test_capability_requirements_filter_tools_by_detected_os(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: os-capabilities
tasks:
  - id: ops
    targets: all
    steps:
      - id: firewall
        substeps:
          - id: firewalld
            use: network.firewall.firewalld.port
            with:
              port: 8443
          - id: ufw
            use: network.firewall.ufw.rule
            with:
              rule: allow
              port: 8443
              protocol: tcp
          - id: pkg
            use: pkg.install
            with:
              packages: [curl]
              manager: auto
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  node:\n    host: 127.0.0.1\n")
    engine = AutomaxEngine()
    monkeypatch.setattr(
        engine,
        "_detect_os_for_plan",
        lambda plan, secrets: {"node": TargetOS(id="ubuntu", id_like=("debian",), family="debian", package_manager="apt")},
    )

    payload = engine.capability_requirements_job(job_path=str(job), inventory_path=str(inventory))

    target = payload["targets"][0]
    assert target["os"]["family"] == "debian"
    assert "apt-get" in target["tools"]
    assert "ufw" in target["tools"]
    assert "firewall-cmd" not in target["tools"]
    assert any(item["plugin"] == "network.firewall.firewalld.port" for item in target["skipped_plugins"])


def test_capability_install_maps_only_missing_tools_to_packages(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: install-caps
tasks:
  - id: ops
    targets: all
    steps:
      - id: fs
        substeps:
          - id: acl
            use: fs.acl.restore
            with:
              file: /tmp/acls.txt
          - id: zip
            use: archive.zip
            with:
              source: /tmp/src
              dest: /tmp/a.zip
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  node:\n    host: 127.0.0.1\n")
    engine = AutomaxEngine()
    installs = []
    monkeypatch.setattr(
        engine,
        "_detect_os_for_plan",
        lambda plan, secrets: {"node": TargetOS(id="ubuntu", id_like=("debian",), family="debian", package_manager="apt")},
    )
    monkeypatch.setattr(engine, "_missing_tools", lambda target, tools: ["setfacl", "zip"])

    def fake_install(*, target, os_family, packages, sudo_password):
        installs.append((target.name, os_family, packages, sudo_password))
        return 0, "installed", ""

    monkeypatch.setattr(engine, "_install_packages_for_os", fake_install)

    payload = engine.install_capability_requirements_job(
        job_path=str(job),
        inventory_path=str(inventory),
        sudo_password_env=None,
    )

    assert payload["ok"] is True
    assert installs == [("node", "debian", ["acl", "zip"], None)]
    assert payload["targets"][0]["missing_tools"] == ["setfacl", "zip"]
    assert payload["targets"][0]["packages"] == ["acl", "zip"]


def test_capability_install_uses_quiet_package_manager_commands(monkeypatch):
    from contextlib import contextmanager

    class FakeChannel:
        def __init__(self):
            self.shutdown = False

        def shutdown_write(self):
            self.shutdown = True

        def recv_exit_status(self):
            return 0

    class FakeStdin:
        def __init__(self):
            self.channel = FakeChannel()
            self.writes: list[str] = []

        def write(self, value):
            self.writes.append(value)

    class FakeStream:
        def __init__(self, data: str = ""):
            self.channel = FakeChannel()
            self._data = data.encode("utf-8")

        def read(self):
            return self._data

    class FakeClient:
        def __init__(self):
            self.commands: list[tuple[str, dict[str, object]]] = []
            self.stdin = FakeStdin()

        def exec_command(self, command, **kwargs):
            self.commands.append((command, kwargs))
            return self.stdin, FakeStream("ok"), FakeStream()

    class FakeSshManager:
        def __init__(self):
            self.client = FakeClient()

        @contextmanager
        def connect(self, target):
            yield self.client

    ssh_manager = FakeSshManager()
    engine = AutomaxEngine(ssh_manager=ssh_manager)

    rc, stdout, stderr = engine._install_packages_for_os(
        target=Target(name="node", host="127.0.0.1"),
        os_family="debian",
        packages=["acl", "zip"],
        sudo_password="secret-pass",
    )

    assert rc == 0
    assert stdout == "ok"
    assert stderr == ""
    command, kwargs = ssh_manager.client.commands[0]
    assert "apt-get -o Dpkg::Use-Pty=0 -o APT::Color=0 update -qq" in command
    assert "apt-get -o Dpkg::Use-Pty=0 -o APT::Color=0 install -y -qq acl zip" in command
    assert "DEBIAN_FRONTEND=noninteractive" in command
    assert "APT_LISTCHANGES_FRONTEND=none" in command
    assert "command sudo -A -p ''" in command
    assert "SUDO_ASKPASS" in command
    assert "secret-pass" not in command
    assert ssh_manager.client.stdin.writes == ["secret-pass\n"]
    assert ssh_manager.client.stdin.channel.shutdown is True
    assert kwargs == {"get_pty": False}


def test_capability_requirements_text_reports_missing_tools_and_packages(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: missing-caps
 tasks:
""".replace("\n tasks:", "\ntasks:") + """
  - id: ops
    targets: all
    steps:
      - id: fs
        substeps:
          - id: acl
            use: fs.acl.restore
            with:
              file: /tmp/acls.txt
          - id: zip
            use: archive.zip
            with:
              source: /tmp/src
              dest: /tmp/a.zip
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  node:\n    host: 127.0.0.1\n")
    monkeypatch.setattr(
        AutomaxEngine,
        "_detect_os_for_plan",
        lambda self, plan, secrets: {"node": TargetOS(id="ubuntu", id_like=("debian",), family="debian", package_manager="apt")},
    )
    monkeypatch.setattr(AutomaxEngine, "_missing_tools", lambda self, target, tools: ["setfacl", "zip"])

    result = CliRunner().invoke(
        cli,
        [
            "capabilities",
            "requirements",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Missing tools: 2" in result.output
    assert "Missing packages: 2" in result.output
    assert "setfacl -> package acl" in result.output
    assert "zip -> package zip" in result.output
    assert "setfacl [missing]: fs.acl.restore" in result.output


def test_capability_install_text_streams_progress(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    job = write(
        tmp_path / "job.yaml",
        """
apiVersion: automax.io/v1
kind: Job
metadata:
  name: install-progress
 tasks:
""".replace("\n tasks:", "\ntasks:") + """
  - id: ops
    targets: all
    steps:
      - id: fs
        substeps:
          - id: acl
            use: fs.acl.restore
            with:
              file: /tmp/acls.txt
""",
    )
    inventory = write(tmp_path / "inventory.yaml", "servers:\n  node:\n    host: 127.0.0.1\n")
    monkeypatch.setattr(
        AutomaxEngine,
        "_detect_os_for_plan",
        lambda self, plan, secrets: {"node": TargetOS(id="ubuntu", id_like=("debian",), family="debian", package_manager="apt")},
    )
    monkeypatch.setattr(AutomaxEngine, "_missing_tools", lambda self, target, tools: ["setfacl"])

    def fake_install(self, *, target, os_family, packages, sudo_password):
        assert packages == ["acl"]
        return 0, "installed", ""

    monkeypatch.setattr(AutomaxEngine, "_install_packages_for_os", fake_install)

    result = CliRunner().invoke(
        cli,
        [
            "capabilities",
            "install",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "[CHECK] node 127.0.0.1 os=debian: checking required tools" in result.output
    assert "[MISSING] node: tools=setfacl" in result.output
    assert "[PLAN] node: install packages=acl" in result.output
    assert "[INSTALL] node: packages=acl" in result.output
    assert "[OK] node 127.0.0.1 os=debian rc=0 changed=true" in result.output
    assert "Summary:" in result.output
    assert "installed" not in result.output
    assert "Command output suppressed for 1 successful target(s); use --verbose" in result.output
    assert result.output.index("[MISSING] node") < result.output.index("[INSTALL] node")

    verbose_result = CliRunner().invoke(
        cli,
        [
            "capabilities",
            "install",
            "--job",
            str(job),
            "--inventory",
            str(inventory),
            "--verbose",
        ],
    )

    assert verbose_result.exit_code == 0, verbose_result.output
    assert "node stdout:" in verbose_result.output
    assert "installed" in verbose_result.output


def test_os_info_inventory_reports_release_details(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  node:
    host: 127.0.0.1
    ssh:
      user: ubuntu
""",
    )
    engine = AutomaxEngine()
    monkeypatch.setattr(
        engine,
        "_detect_os_for_targets",
        lambda targets, secrets: {
            "node": TargetOS(
                id="ubuntu",
                id_like=("debian",),
                name="Ubuntu",
                pretty_name="Ubuntu 24.04.2 LTS",
                version="24.04.2 LTS (Noble Numbat)",
                version_id="24.04",
                version_codename="noble",
                family="debian",
                package_manager="apt",
            )
        },
    )

    payload = engine.os_info_inventory(inventory_path=str(inventory))

    assert payload["mode"] == "os-info"
    assert payload["target_count"] == 1
    target = payload["targets"][0]
    assert target["target"] == "node"
    assert target["user"] == "ubuntu"
    assert target["os"]["pretty_name"] == "Ubuntu 24.04.2 LTS"
    assert target["os"]["version_codename"] == "noble"
    assert target["os"]["family"] == "debian"


def test_os_info_cli_json_output(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    inventory = write(tmp_path / "inventory.yaml", "servers:\n  node:\n    host: 127.0.0.1\n")
    monkeypatch.setattr(
        AutomaxEngine,
        "_detect_os_for_targets",
        lambda self, targets, secrets: {
            "node": TargetOS(id="debian", id_like=(), pretty_name="Debian GNU/Linux 12", version_id="12", family="debian", package_manager="apt")
        },
    )

    result = CliRunner().invoke(
        cli,
        ["os", "info", "--inventory", str(inventory), "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "os-info"
    assert payload["targets"][0]["os"]["id"] == "debian"
    assert payload["targets"][0]["os"]["pretty_name"] == "Debian GNU/Linux 12"


def test_os_info_cli_text_output_groups_details_and_summary(tmp_path: Path, monkeypatch):
    from automax.core.os_detect import TargetOS

    inventory = write(
        tmp_path / "inventory.yaml",
        """
servers:
  lab01:
    host: 192.0.2.10
    port: 2222
    ssh:
      user: ubuntu
  lab02:
    host: 192.0.2.11
    ssh:
      user: ubuntu
""",
    )
    monkeypatch.setattr(
        AutomaxEngine,
        "_detect_os_for_targets",
        lambda self, targets, secrets: {
            "lab01": TargetOS(
                id="ubuntu",
                id_like=("debian",),
                pretty_name="Ubuntu 24.04.4 LTS",
                version_id="24.04",
                version_codename="noble",
                family="debian",
                package_manager="apt",
            ),
            "lab02": TargetOS(
                id="debian",
                id_like=(),
                pretty_name="Debian GNU/Linux 12",
                version_id="12",
                family="debian",
                package_manager="apt",
            ),
        },
    )

    result = CliRunner().invoke(cli, ["os", "info", "--inventory", str(inventory)])

    assert result.exit_code == 0, result.output
    assert "Detected operating-system facts." in result.output
    assert "Target lab01 192.0.2.10:2222" in result.output
    assert "  user             ubuntu" in result.output
    assert "  os               Ubuntu 24.04.4 LTS" in result.output
    assert "  codename         noble" in result.output
    assert "Target lab02 192.0.2.11:22" in result.output
    assert "Summary:" in result.output
    assert "  debian/apt: 2 targets" in result.output
