# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Command-line interface for Automax next engine.
"""

from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, Iterable
from pathlib import Path
import json

import click

from automax import __version__
from automax.core.engine import AutomaxEngine, AutomaxError
from automax.core.plugin_docs import render_plugin_reference
from automax.core.schema import export_schema
from automax.core.job_views import render_dot, render_explain_text, render_mermaid, render_runbook_markdown, render_svg
from automax.core.models import NodeStatus
from automax.core.state import StateStore
from automax.plugins.registry import build_builtin_registry


def _parse_vars(values: Iterable[str]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise click.ClickException(f"Invalid --var format: {value}. Use KEY=VALUE")
        key, raw = value.split("=", 1)
        parsed[key.strip()] = raw.strip()
    return parsed


def _split_selectors(values: Iterable[str]) -> list[str]:
    selectors: list[str] = []
    for value in values:
        for item in str(value).split(","):
            item = item.strip()
            if item:
                selectors.append(item)
    return selectors


def _engine(extra_plugin_path: tuple[str, ...] = ()) -> AutomaxEngine:
    return AutomaxEngine(plugin_registry=build_builtin_registry(extra_plugin_path))


def _echo_check_payload(payload: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo(f"Job: {payload['job']}")
    click.echo("Check mode preview:")
    for node in payload["nodes"]:
        changed = str(node["changed"]).lower()
        support = "check" if node["supports_check_mode"] else "dry-run"
        params = json.dumps(node["params"], sort_keys=True)
        click.echo(
            f"CHECK {node['target']} {node['node_id']} {node['plugin']} "
            f"support={support} changed={changed} {node['message']} "
            f"params={params}".rstrip()
        )
    if not payload["nodes"]:
        click.echo("  - no selected nodes")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="Automax")
def cli() -> None:
    """Automax - YAML-driven SSH automation engine."""


_COMMON_OPTIONS = [
    click.option("--job", "job_path", required=True, type=click.Path(exists=True), help="External job YAML path."),
    click.option("--inventory", "inventory_path", required=True, type=click.Path(exists=True), help="External inventory YAML path."),
    click.option("--vars", "vars_path", type=click.Path(exists=True), help="External variables YAML path."),
    click.option("--secrets", "secrets_path", type=click.Path(exists=True), help="External secrets YAML path."),
    click.option("--var", "cli_vars", multiple=True, help="Override variable, format KEY=VALUE."),
]


def _apply_common_options(function):
    for option in reversed(_COMMON_OPTIONS):
        function = option(function)
    return function


@cli.command()
@_apply_common_options
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
@click.option("--from", "from_node", help="Start from task/step/substep checkpoint node.")
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Run only substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Skip substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--dry-run", is_flag=True, help="Validate and simulate actions without changing targets.")
@click.option("--check", "check_mode", is_flag=True, help="Render a check-mode preview without creating run state.")
@click.option("--lock", is_flag=True, help="Acquire job/target locks before executing.")
@click.option("--lock-scope", type=click.Choice(["job", "target", "both"]), default="both", show_default=True, help="Lock job, targets or both.")
@click.option("--lock-timeout", type=float, default=0.0, show_default=True, help="Seconds to wait for locks.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", show_default=True, help="Output format for the final run summary.")
def run(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    state_dir: str,
    from_node: str | None,
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    dry_run: bool,
    check_mode: bool,
    lock: bool,
    lock_scope: str,
    lock_timeout: float,
    output_format: str,
) -> None:
    """Run a job from external YAML definitions."""
    try:
        engine = _engine(plugin_path)
        if check_mode:
            payload = engine.check_job(
                job_path=job_path,
                inventory_path=inventory_path,
                vars_path=vars_path,
                secrets_path=secrets_path,
                limit=_split_selectors(limit),
                exclude=_split_selectors(exclude),
                tags=_split_selectors(tags),
                skip_tags=_split_selectors(skip_tags),
                cli_vars=_parse_vars(cli_vars),
            )
            _echo_check_payload(payload, output_format)
            if not payload["ok"]:
                raise click.ClickException("check-mode preview found errors")
            return
        rc = engine.run(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            state_dir=state_dir,
            dry_run=dry_run,
            from_node=from_node,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
            output_format=output_format,
            lock=lock,
            lock_scope=lock_scope,
            lock_timeout=lock_timeout,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    sys.exit(rc)


@cli.command()
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Show only substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Hide substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--check", "check_mode", is_flag=True, help="Render a check-mode preview instead of the execution plan.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", show_default=True, help="Output format for the execution plan.")
def plan(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    check_mode: bool,
    output_format: str,
) -> None:
    """Print the execution plan without running the job."""
    try:
        engine = _engine(plugin_path)
        if check_mode:
            payload = engine.check_job(
                job_path=job_path,
                inventory_path=inventory_path,
                vars_path=vars_path,
                secrets_path=secrets_path,
                limit=_split_selectors(limit),
                exclude=_split_selectors(exclude),
                tags=_split_selectors(tags),
                skip_tags=_split_selectors(skip_tags),
                cli_vars=_parse_vars(cli_vars),
            )
            _echo_check_payload(payload, output_format)
            if not payload["ok"]:
                raise click.ClickException("check-mode preview found errors")
            return
        rc = engine.run(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            plan_only=True,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
            output_format=output_format,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    sys.exit(rc)



@cli.command()
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Explain only substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Hide substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", show_default=True, help="Explanation output format.")
def explain(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    output_format: str,
) -> None:
    """Explain the resolved job flow, targets and resume points without creating run state."""
    try:
        view = _engine(plugin_path).inspect_job(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    if output_format == "json":
        click.echo(json.dumps(view, indent=2, sort_keys=True))
        return
    click.echo(render_explain_text(view), nl=False)



@cli.command()
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Graph only substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Hide substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--format", "output_format", type=click.Choice(["mermaid", "dot", "svg", "png"]), default="mermaid", show_default=True, help="Graph output format.")
@click.option("--output", "output_path", type=click.Path(dir_okay=False), help="Output path. Defaults to stdout for text formats.")
def graph(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    output_format: str,
    output_path: str | None,
) -> None:
    """Render the resolved job flow as Mermaid, DOT, SVG or PNG."""
    try:
        view = _engine(plugin_path).inspect_job(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    if output_format == "mermaid":
        rendered = render_mermaid(view)
    elif output_format == "dot":
        rendered = render_dot(view)
    elif output_format == "svg":
        rendered = render_svg(view)
    else:
        dot = shutil.which("dot")
        if not dot:
            raise click.ClickException("PNG graph output requires Graphviz 'dot' in PATH")
        if not output_path:
            raise click.ClickException("--output is required for PNG graph output")
        subprocess.run([dot, "-Tpng", "-o", output_path], input=render_dot(view), text=True, check=True)
        click.echo(f"Wrote {output_path}")
        return
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        click.echo(f"Wrote {output}")
        return
    click.echo(rendered, nl=False)



@cli.group()
def runbook() -> None:
    """Generate operator runbooks from resolved jobs."""


@runbook.command("export")
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Export only substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Hide substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--format", "output_format", type=click.Choice(["markdown"]), default="markdown", show_default=True, help="Runbook output format.")
@click.option("--output", "output_path", type=click.Path(dir_okay=False), help="Output file path. Defaults to stdout.")
def export_runbook(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    output_format: str,
    output_path: str | None,
) -> None:
    """Export a Markdown runbook from a resolved job."""
    try:
        view = _engine(plugin_path).inspect_job(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    if output_format != "markdown":
        raise click.ClickException(f"unsupported runbook format: {output_format}")
    rendered = render_runbook_markdown(view)
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        click.echo(f"Wrote {output}")
        return
    click.echo(rendered, nl=False)


@cli.command()
@_apply_common_options
@click.option("--tags", multiple=True, help="Validate plan after keeping only these tags.")
@click.option("--skip-tags", multiple=True, help="Validate plan after skipping these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--strict", is_flag=True, help="Reject unknown DSL keys and plugin parameters.")
def validate(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    strict: bool,
) -> None:
    """Validate job, inventory, variables, secrets and plugin parameters."""
    try:
        _engine(plugin_path).validate(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            cli_vars=_parse_vars(cli_vars),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            strict=strict,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    suffix = " strict" if strict else ""
    click.echo(f"Validation{suffix} successful")


@cli.command()
@click.argument("path", type=click.Path(file_okay=False, dir_okay=True))
@click.option("--force", is_flag=True, help="Overwrite generated files when they already exist.")
def init(path: str, force: bool) -> None:
    """Create an external Automax workspace skeleton."""
    root = Path(path).expanduser().resolve()
    files = {
        "jobs/local-smoke.yaml": """apiVersion: automax.io/v1
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
              command: \"printf 'hello from automax\\n'\"
""",
        "inventory/local.yaml": """servers:
  controller:
    host: 127.0.0.1
""",
        "vars/local.yaml": """vars:
  message: hello
""",
        "secrets/local.example.yaml": """secrets:
  demo:
    provider: env
    name: AUTOMAX_DEMO_SECRET
""",
        "templates/example.conf.j2": """message={{ vars.message }}
""",
        "README.md": """# Automax workspace

Run the local smoke job with:

```bash
automax validate --strict \
  --job jobs/local-smoke.yaml \
  --inventory inventory/local.yaml \
  --vars vars/local.yaml

automax run \
  --job jobs/local-smoke.yaml \
  --inventory inventory/local.yaml \
  --vars vars/local.yaml
```
""",
    }
    created = []
    for relative, content in files.items():
        destination = root / relative
        if destination.exists() and not force:
            raise click.ClickException(f"refusing to overwrite existing file: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        created.append(destination)
    click.echo(f"Initialized Automax workspace: {root}")
    for item in created:
        click.echo(f"  {item.relative_to(root)}")


@cli.command()
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory to check.")
@click.option("--json", "as_json", is_flag=True, help="Print structured JSON diagnostics.")
def doctor(state_dir: str, as_json: bool) -> None:
    """Inspect the local Automax runtime environment."""
    checks = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    version = sys.version_info
    add("python", version >= (3, 9), platform.python_version())
    add("automax", True, __version__)
    add("paramiko", importlib.util.find_spec("paramiko") is not None, "installed" if importlib.util.find_spec("paramiko") else "missing")
    for module, label in (("sqlite3", "sqlite"), ("psycopg", "postgres"), ("pymysql", "mysql"), ("oracledb", "oracle")):
        add(f"database.{label}", importlib.util.find_spec(module) is not None, "installed" if importlib.util.find_spec(module) else "optional driver missing")
    add("mkdocs", importlib.util.find_spec("mkdocs") is not None, "installed" if importlib.util.find_spec("mkdocs") else "optional docs extra missing")
    path = Path(state_dir).expanduser().resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        add("state-dir", True, str(path))
    except Exception as exc:
        add("state-dir", False, f"{path}: {exc}")
    add("ssh", shutil.which("ssh") is not None, shutil.which("ssh") or "ssh executable not found")
    add("plugins", True, f"{len(build_builtin_registry().names())} builtin plugins")

    blocking = {"python", "state-dir", "plugins"}
    payload = {
        "ok": all(item["ok"] for item in checks if item["name"] in blocking),
        "checks": checks,
    }
    if as_json:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        click.echo("Automax doctor")
        for item in checks:
            status = "OK" if item["ok"] else "WARN"
            click.echo(f"  {status:<4} {item['name']}: {item['detail']}")
    if not payload["ok"]:
        raise click.ClickException("doctor found blocking issues")


@cli.command()
@click.argument("run_id")
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
@click.option("--from", "from_node", help="Override restart checkpoint node.")
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Resume only substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Skip substeps matching one of these tags.")
@click.option("--var", "cli_vars", multiple=True, help="Override variable, format KEY=VALUE.")
@click.option("--skip-successful", is_flag=True, help="Do not rerun nodes already marked successful in this run.")
@click.option("--only-failed", is_flag=True, help="Rerun only nodes currently marked failed in this run.")
@click.option("--dry-run", is_flag=True, help="Validate and simulate actions without changing targets.")
@click.option("--check", "check_mode", is_flag=True, help="Render a check-mode preview without creating run state.")
@click.option("--lock", is_flag=True, help="Acquire job/target locks before executing.")
@click.option("--lock-scope", type=click.Choice(["job", "target", "both"]), default="both", show_default=True, help="Lock job, targets or both.")
@click.option("--lock-timeout", type=float, default=0.0, show_default=True, help="Seconds to wait for locks.")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", show_default=True, help="Output format for the final resume summary.")
def resume(
    run_id: str,
    state_dir: str,
    from_node: str | None,
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    cli_vars: tuple[str, ...],
    skip_successful: bool,
    only_failed: bool,
    dry_run: bool,
    check_mode: bool,
    lock: bool,
    lock_scope: str,
    lock_timeout: float,
    output_format: str,
) -> None:
    """Resume an existing run from failed or explicit checkpoint."""
    try:
        rc = _engine().resume(
            run_id=run_id,
            state_dir=state_dir,
            from_node=from_node,
            dry_run=dry_run,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
            skip_successful=skip_successful,
            only_failed=only_failed,
            output_format=output_format,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    sys.exit(rc)


@cli.group()
def secrets() -> None:
    """Inspect job-scoped secret definitions."""


@secrets.command("check")
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Check secrets for substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Skip substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--all", "include_all", is_flag=True, help="Include declared secrets not used by the selected job plan.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def check_secrets(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    include_all: bool,
    output_format: str,
) -> None:
    """Check the secrets needed by one resolved job without printing values."""
    try:
        payload = _engine(plugin_path).check_secrets(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
            include_all=include_all,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        click.echo(f"Job: {payload['job']}")
        click.echo(f"Secrets: {payload['secrets_path'] or '-'}")
        for item in payload["secrets"]:
            used = "used" if item.get("used") else "unused"
            click.echo(
                f"{item['name']}  {item['provider']}  "
                f"{item['status']}  {used}  {item['detail']}"
            )
        if not payload["secrets"]:
            click.echo("No secrets referenced by selected job plan")
    if not payload["ok"]:
        raise click.ClickException("one or more secrets failed checks")


@cli.group()
def inventory() -> None:
    """Inspect job-scoped inventory resolution."""


@inventory.command("show")
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Show targets for substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Hide substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def show_inventory(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
    output_format: str,
) -> None:
    """Show inventory targets selected by the resolved job."""
    try:
        payload = _engine(plugin_path).inspect_inventory(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    click.echo(f"Job: {payload['job']}")
    click.echo(f"Inventory: {payload['inventory_path']}")
    click.echo(
        f"Targets: {payload['target_count']} selected, "
        f"{payload['node_count']} planned node(s)"
    )
    for target in payload["targets"]:
        groups = ",".join(target["groups"]) if target["groups"] else "-"
        user = target["user"] or "-"
        click.echo(
            f"{target['name']}  {target['host']}:{target['port']}  "
            f"user={user} groups={groups} nodes={target['nodes']}"
        )


@cli.group()
def runs() -> None:
    """Inspect stored run states."""


@runs.command("list")
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
def list_runs(state_dir: str) -> None:
    """List known runs from a state directory."""
    for run in StateStore.list_all_runs(state_dir):
        click.echo(f"{run['run_id']} {run['status']} {run['created_at']} {run['job_path']}")


@runs.command("show")
@click.argument("run_id")
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
@click.option("--failed", "failed_only", is_flag=True, help="Show only failed nodes in the node table.")
@click.option("--server", "server_name", help="Show node details for one target/server.")
@click.option("--json", "as_json", is_flag=True, help="Print structured JSON output.")
def show_run(run_id: str, state_dir: str, failed_only: bool, server_name: str | None, as_json: bool) -> None:
    """Show one run summary, failed checkpoints and optional node details."""
    store = StateStore.open_existing(state_dir, run_id)
    summary = store.summarize()
    statuses = {NodeStatus.FAILED.value} if failed_only else None
    nodes = store.list_nodes(statuses=statuses, target=server_name) if (failed_only or server_name) else []

    if as_json:
        payload: Dict[str, Any] = dict(summary)
        payload["nodes"] = nodes
        click.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return

    run = summary["run"]
    click.echo(f"Run: {run_id}")
    click.echo(f"Status: {run['status']}")
    click.echo(f"Job: {run['job_path']}")
    click.echo(f"Inventory: {run.get('inventory_path') or '-'}")
    click.echo(f"Vars: {run.get('vars_path') or '-'}")
    click.echo(f"Secrets: {run.get('secrets_path') or '-'}")
    click.echo(f"Created: {run['created_at']}")
    click.echo(f"Updated: {run['updated_at']}")
    click.echo(f"State: {store.run_dir}")
    click.echo("Summary:")
    click.echo(f"  targets: {summary['targets_total']}")
    click.echo(f"  nodes: {summary['nodes_total']}")
    click.echo(f"  success: {summary['status_counts'].get(NodeStatus.SUCCESS.value, 0)}")
    click.echo(f"  warning: {summary['status_counts'].get(NodeStatus.WARNING.value, 0)}")
    click.echo(f"  failed: {summary['status_counts'].get(NodeStatus.FAILED.value, 0)}")
    click.echo(f"  skipped: {summary['status_counts'].get(NodeStatus.SKIPPED.value, 0)}")
    click.echo(f"  changed: {summary['changed_nodes']}")
    click.echo(f"  artifacts: {summary['artifacts_count']}")

    if summary["targets"]:
        click.echo("Targets:")
        for target in summary["targets"]:
            counts = target["status_counts"]
            click.echo(
                "  "
                f"{target['target']} {target['status']} "
                f"changed={target['changed']} "
                f"success={counts.get(NodeStatus.SUCCESS.value, 0)} "
                f"warning={counts.get(NodeStatus.WARNING.value, 0)} "
                f"failed={counts.get(NodeStatus.FAILED.value, 0)} "
                f"skipped={counts.get(NodeStatus.SKIPPED.value, 0)}"
            )

    warning_nodes = summary.get("warning_nodes", [])
    if warning_nodes:
        click.echo("Warning nodes:")
        for node in warning_nodes:
            message = f" {node['message']}" if node.get("message") else ""
            click.echo(f"  {node['target']} {node['node_id']} rc={node['rc']}{message}".rstrip())

    failed_nodes = summary["failed_nodes"]
    if failed_nodes:
        click.echo("Failed nodes:")
        for node in failed_nodes:
            message = f" {node['message']}" if node.get("message") else ""
            click.echo(f"  {node['target']} {node['node_id']} rc={node['rc']}{message}".rstrip())
        first_failed = failed_nodes[0]["node_id"]
        click.echo("Resume:")
        click.echo(f"  automax resume {run_id} --state-dir {state_dir} --skip-successful")
        click.echo(f"  automax resume {run_id} --state-dir {state_dir} --only-failed")
        click.echo(f"  automax resume {run_id} --state-dir {state_dir} --from {first_failed}")

    if failed_only or server_name:
        click.echo("Nodes:")
        if not nodes:
            click.echo("  - none")
        for node in nodes:
            message = f" {node['message']}" if node.get("message") else ""
            click.echo(
                f"  {node['target']} {node['status']} {node['node_id']} "
                f"changed={str(node['changed']).lower()} rc={node['rc']}{message}".rstrip()
            )

    if summary["artifacts_count"]:
        click.echo("Artifacts:")
        click.echo(f"  automax artifacts list {run_id} --state-dir {state_dir}")


@cli.group()
def plugins() -> None:
    """Inspect plugins."""


@plugins.command("list")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--include-aliases", is_flag=True, help="Also show plugin aliases, when external plugins define them.")
def list_plugins(plugin_path: tuple[str, ...], include_aliases: bool) -> None:
    """List canonical registered builtin and external plugin names."""
    registry = build_builtin_registry(plugin_path)
    for name in registry.names(include_aliases=include_aliases):
        click.echo(name)



@plugins.command("describe")
@click.argument("name")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--json", "as_json", is_flag=True, help="Print structured JSON metadata.")
def describe_plugin(name: str, plugin_path: tuple[str, ...], as_json: bool) -> None:
    """Describe one registered plugin and its parameters."""
    try:
        description = build_builtin_registry(plugin_path).describe(name)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps(description, indent=2, sort_keys=True))
        return

    click.echo(f"Name: {description['name']}")
    click.echo(f"Category: {description['category']}")
    click.echo(f"Description: {description['description'] or '-'}")
    click.echo(f"Remote session: {str(description['opens_remote_session']).lower()}")
    click.echo(f"Dry-run support: {str(description['supports_dry_run']).lower()}")
    click.echo(f"Check mode support: {str(description['supports_check_mode']).lower()}")

    required = description['required_params'] or []
    optional = description['optional_params'] or []
    aliases = description['aliases'] or []
    click.echo("Required params:")
    for item in required:
        click.echo(f"  - {item}")
    if not required:
        click.echo("  - none")

    click.echo("Optional params:")
    for item in optional:
        click.echo(f"  - {item}")
    if not optional:
        click.echo("  - none")

    parameters = description.get("parameters") or []
    if parameters:
        click.echo("Parameters:")
        for parameter in parameters:
            marker = "required" if parameter.get("required") else "optional"
            default = parameter.get("default")
            default_text = f", default={default}" if default is not None else ""
            desc = parameter.get("description") or "-"
            click.echo(
                f"  - {parameter['name']} ({marker}, {parameter.get('type', 'any')}{default_text}): {desc}"
            )

    result_fields = description.get("result_fields") or {}
    if result_fields:
        click.echo("Result fields:")
        for key, value in result_fields.items():
            click.echo(f"  - {key}: {value}")

    examples = description.get("examples") or []
    if examples:
        click.echo("Examples:")
        for item in examples:
            click.echo("---")
            click.echo(item)

    if aliases:
        click.echo("Aliases:")
        for item in aliases:
            click.echo(f"  - {item}")





@cli.group()
def artifacts() -> None:
    """Inspect files captured during a run."""


@artifacts.command("path")
@click.argument("run_id")
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
def artifacts_path(run_id: str, state_dir: str) -> None:
    """Print the artifact directory for one run."""
    store = StateStore.open_existing(state_dir, run_id)
    click.echo(str(store.artifacts_dir))


@artifacts.command("list")
@click.argument("run_id")
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
def artifacts_list(run_id: str, state_dir: str) -> None:
    """List artifacts captured for one run."""
    store = StateStore.open_existing(state_dir, run_id)
    for item in store.list_artifacts():
        click.echo(
            f"{item['target']} {item['node_id']} {item['kind']} {item['name']} "
            f"{item['size']}B {item['path']}"
        )


@cli.group()
def docs() -> None:
    """Generate documentation from runtime metadata."""


@docs.command("generate-plugins")
@click.option("--output", "output_path", required=True, type=click.Path(dir_okay=False), help="Markdown output path.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
def generate_plugin_docs(output_path: str, plugin_path: tuple[str, ...]) -> None:
    """Generate Markdown plugin reference from structured metadata."""
    registry = build_builtin_registry(plugin_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_plugin_reference(registry.describe_all()), encoding="utf-8")
    click.echo(f"Wrote {output}")


@cli.group()
def schema() -> None:
    """Export machine-readable Automax schemas."""


@schema.command("export")
@click.option(
    "--kind",
    type=click.Choice(["job", "inventory", "vars", "secrets", "all"]),
    default="job",
    show_default=True,
    help="Schema kind to export.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json"]),
    default="json",
    show_default=True,
    help="Schema output format. JSON is currently supported; the option is reserved for future formats.",
)
@click.option("--output", "output_path", type=click.Path(dir_okay=False), help="Output file path. Defaults to stdout.")
def export_schema_command(kind: str, output_format: str, output_path: str | None) -> None:
    """Export the Automax YAML contract as JSON Schema."""
    if output_format != "json":
        raise click.ClickException(f"unsupported schema format: {output_format}")
    payload = json.dumps(export_schema(kind), indent=2, sort_keys=True) + "\n"
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
        click.echo(f"Wrote {output}")
        return
    click.echo(payload, nl=False)


def cli_main() -> None:
    """Console-script entry point."""
    cli()


if __name__ == "__main__":
    cli_main()
