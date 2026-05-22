# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Command-line interface for Automax next engine.
"""

from __future__ import annotations

import sys
from typing import Dict, Iterable
import json

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
@click.option("--skip-successful", is_flag=True, help="Do not rerun nodes already marked successful in this run.")
@click.option("--only-failed", is_flag=True, help="Rerun only nodes currently marked failed in this run.")
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
    skip_successful: bool,
    only_failed: bool,
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
            skip_successful=skip_successful,
            only_failed=only_failed,
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

def cli_main() -> None:
    """Console-script entry point."""
    cli()


if __name__ == "__main__":
    cli_main()
