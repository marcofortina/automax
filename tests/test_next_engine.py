from __future__ import annotations

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from automax.cli.cli import cli
from automax.core.engine import AutomaxEngine
from automax.core.models import ExecutionContext, Target
from automax.core.state import StateStore
from automax.plugins.base import PluginValidationError
from automax.plugins.fs_extra import FsSymlinkCreatePlugin, FsSymlinkRemovePlugin


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
    expected_names = {
        "archive.tar",
        "archive.untar",
        "archive.zip",
        "archive.unzip",
        "fs.cd",
        "fs.chmod",
        "fs.chown",
        "fs.copy",
        "fs.exists",
        "fs.find",
        "fs.line",
        "fs.mkdir",
        "fs.move",
        "fs.read",
        "fs.remove",
        "fs.replace",
        "fs.stat",
        "fs.symlink.create",
        "fs.symlink.remove",
        "fs.template",
        "fs.write",
        "local.command",
        "pkg.install",
        "pkg.query",
        "pkg.remove",
        "pkg.update_cache",
        "pkg.upgrade",
        "process.kill",
        "process.wait",
        "remote.command",
        "systemctl.daemon_reload",
        "systemctl.disable",
        "systemctl.enable",
        "systemctl.is_active",
        "systemctl.is_enabled",
        "systemctl.mask",
        "systemctl.reload",
        "systemctl.restart",
        "systemctl.start",
        "systemctl.status",
        "systemctl.stop",
        "systemctl.unmask",
        "transfer.download",
        "transfer.sync",
        "transfer.upload",
        "user.create",
        "user.modify",
        "user.remove",
        "group.create",
        "group.remove",
        "http.assert",
        "http.request",
        "http.wait",
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
        "db.sqlite.query",
        "db.postgres.query",
        "db.mysql.query",
        "db.oracle.query",
    }
    assert output_names == expected_names
    assert "local_command" not in output_names
    assert "ssh_command" not in output_names
    assert "tar" not in output_names
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

    import automax.plugins.fs_extra as fs_extra

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

    create_result = FsSymlinkCreatePlugin().execute(
        {"src": "/opt/app/releases/1", "dest": "/opt/app/current", "force": True},
        context,
    )
    remove_result = FsSymlinkRemovePlugin().execute(
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
        FsSymlinkCreatePlugin().validate({"src": "/tmp/source", "dest": "/"})
    with pytest.raises(PluginValidationError):
        FsSymlinkRemovePlugin().validate({"path": "/"})


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
