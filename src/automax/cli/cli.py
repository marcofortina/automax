# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Command-line interface for Automax next engine.
"""

from __future__ import annotations

import sys
from typing import Dict, Iterable

import click

from automax import __version__
from automax.core.engine import AutomaxEngine, AutomaxError
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
) -> None:
    """Run a job from external YAML definitions."""
    try:
        rc = _engine(plugin_path).run(
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
) -> None:
    """Print the execution plan without running the job."""
    try:
        rc = _engine(plugin_path).run(
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
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    sys.exit(rc)


@cli.command()
@_apply_common_options
@click.option("--tags", multiple=True, help="Validate plan after keeping only these tags.")
@click.option("--skip-tags", multiple=True, help="Validate plan after skipping these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
def validate(
    job_path: str,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    plugin_path: tuple[str, ...],
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
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo("Validation successful")


@cli.command()
@click.argument("run_id")
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
@click.option("--from", "from_node", help="Override restart checkpoint node.")
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Resume only substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Skip substeps matching one of these tags.")
@click.option("--var", "cli_vars", multiple=True, help="Override variable, format KEY=VALUE.")
@click.option("--dry-run", is_flag=True, help="Validate and simulate actions without changing targets.")
def resume(
    run_id: str,
    state_dir: str,
    from_node: str | None,
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    tags: tuple[str, ...],
    skip_tags: tuple[str, ...],
    cli_vars: tuple[str, ...],
    dry_run: bool,
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
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    sys.exit(rc)


@cli.group()
def runs() -> None:
    """Inspect stored run states."""


@runs.command("list")
@click.option("--state-dir", default=".automax/runs", show_default=True, help="Run state directory.")
def list_runs(state_dir: str) -> None:
    """List known runs from a state directory."""
    for run in StateStore.list_all_runs(state_dir):
        click.echo(f"{run['run_id']} {run['status']} {run['created_at']} {run['job_path']}")


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


def cli_main() -> None:
    """Console-script entry point."""
    cli()


if __name__ == "__main__":
    cli_main()
