# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Command-line interface for Automax engine.
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
from automax.core.capabilities import package_for_tool
from automax.core.inventory import Inventory, InventoryError, load_inventory_document
from automax.core.known_hosts import KnownHostEntry, KnownHostsError, scan_known_hosts, write_known_hosts
from automax.core.plugin_docs import render_plugin_reference
from automax.core.schema import export_schema
from automax.core.job_views import render_dot, render_explain_text, render_mermaid, render_runbook_markdown, render_svg
from automax.core.models import NodeStatus, Target
from automax.core.state import StateStore
from automax.core.yaml_loader import load_yaml_file
from automax.plugins.audit import audit_plugin_registry
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


def _echo_diff_payload(payload: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo(f"Job: {payload['job']}")
    click.echo("Diff preview:")
    for item in payload["diffs"]:
        if item.get("available", True):
            click.echo(f"# {item['target']} {item['node_id']} {item['plugin']} {item['path']}")
            click.echo(item["diff"], nl=False)
        else:
            click.echo(f"# {item['target']} {item['node_id']} {item['plugin']} no deterministic diff: {item['reason']}")
    if not payload["diffs"]:
        click.echo("  - no selected nodes")


def _echo_check_detail(payload: Dict[str, Any]) -> None:
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


def _echo_check_summary(payload: Dict[str, Any]) -> None:
    nodes = list(payload["nodes"])
    click.echo(f"Job: {payload['job']}")
    click.echo("Mode: check")
    if not nodes:
        click.echo("Check preview: no selected nodes")
        click.echo("Result: OK")
        return

    target_names = sorted({str(node["target"]) for node in nodes})
    task_groups: Dict[str, list[Dict[str, Any]]] = {}
    for node in nodes:
        task_groups.setdefault(str(node["task_id"]), []).append(node)

    click.echo(f"Targets: {', '.join(target_names)}")
    click.echo("")
    click.echo("Check preview:")
    for task_id, group in task_groups.items():
        task_targets = {str(node["target"]) for node in group}
        task_substeps = {str(node["node_id"]) for node in group}
        failures = sum(1 for node in group if not node["ok"])
        changed = sum(1 for node in group if node["changed"])
        status = "FAILED" if failures else "OK"
        suffix = f" changed={changed}" if changed else ""
        substep_count = len(task_substeps)
        target_count = len(task_targets)
        substep_label = "substep" if substep_count == 1 else "substeps"
        target_label = "target" if target_count == 1 else "targets"
        click.echo(
            f"  {task_id:<20} {substep_count:>3} {substep_label:<8} x "
            f"{target_count:>2} {target_label:<7} {status}{suffix}"
        )

    check_support = sum(1 for node in nodes if node["supports_check_mode"])
    dry_run_support = len(nodes) - check_support
    changed_count = sum(1 for node in nodes if node["changed"])
    failure_count = sum(1 for node in nodes if not node["ok"])
    click.echo("")
    click.echo("Summary:")
    click.echo(f"  targets:        {len(target_names)}")
    click.echo(f"  tasks:          {len(task_groups)}")
    click.echo(f"  substeps:       {len({str(node['node_id']) for node in nodes})}")
    click.echo(f"  previews:       {len(nodes)}")
    click.echo(f"  check support:  {check_support}")
    click.echo(f"  dry-run support:{dry_run_support:>3}")
    click.echo(f"  changed:        {changed_count}")
    click.echo(f"  failures:       {failure_count}")

    if failure_count:
        click.echo("")
        click.echo("Failures:")
        for node in nodes:
            if not node["ok"]:
                click.echo(f"  {node['target']} {node['node_id']} {node['plugin']}: {node['message']}")

    result = "OK" if payload["ok"] else "FAILED"
    click.echo(f"Result: {result}")
    click.echo("Use --verbose to show per-target substep details.")


def _echo_check_payload(payload: Dict[str, Any], output_format: str, *, verbose: bool = True) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    if verbose:
        _echo_check_detail(payload)
        return
    _echo_check_summary(payload)


def _echo_vars_payload(payload: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo(f"Job: {payload['job']}")
    click.echo(f"Vars: {payload['vars_path'] or '-'}")
    click.echo(f"Secrets: {payload['secrets_path'] or '-'}")
    click.echo(
        f"Targets: {payload['target_count']} selected, "
        f"{payload['node_count']} planned node(s)"
    )
    for target in payload["targets"]:
        groups = ",".join(target["groups"]) if target["groups"] else "-"
        click.echo(f"Target {target['name']} {target['host']}:{target['port']} groups={groups}")
        click.echo("  vars:")
        if target["vars"]:
            for key in sorted(target["vars"]):
                click.echo(f"    {key}: {json.dumps(target['vars'][key], sort_keys=True)}")
        else:
            click.echo("    - none")
        click.echo("  secrets:")
        if target["secrets"]:
            for key in sorted(target["secrets"]):
                click.echo(f"    {key}: ***")
        else:
            click.echo("    - none")
        click.echo("  nodes:")
        for node in target["nodes"]:
            click.echo(f"    {node['node_id']} {node['plugin']}")


def _package_for_display(tool: str, target: Dict[str, Any]) -> str | None:
    family = target.get("os", {}).get("family", "unknown")
    return package_for_tool(tool, family)


def _echo_capabilities_payload(payload: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo(f"Job: {payload['job']}")
    click.echo(
        f"Targets: {payload['target_count']}  "
        f"Tools: {payload['tool_count']}  "
        f"Packages: {payload.get('package_count', 0)}  "
        f"Missing tools: {payload.get('missing_tool_count', 0)}  "
        f"Missing packages: {payload.get('missing_package_count', 0)}"
    )
    for target in payload["targets"]:
        click.echo(f"Target {target['target']} {target['host']} os={target.get('os', {}).get('family', 'unknown')} id={target.get('os', {}).get('id', 'unknown')}")
        if target.get("skipped_plugins"):
            click.echo("  skipped OS-mismatched plugins:")
            for skipped in target["skipped_plugins"]:
                click.echo(f"    {skipped['plugin']}: {skipped['reason']}")
        if target.get("packages"):
            click.echo("  required packages:")
            for package in target["packages"]:
                click.echo(f"    {package}")
        if "missing_tools" in target:
            if target.get("missing_tools"):
                click.echo("  missing tools:")
                for tool in target["missing_tools"]:
                    package = _package_for_display(tool, target)
                    suffix = f" -> package {package}" if package else " -> package unknown"
                    click.echo(f"    {tool}{suffix}")
            else:
                click.echo("  missing tools: none")
            if target.get("missing_packages"):
                click.echo("  missing packages:")
                for package in target["missing_packages"]:
                    click.echo(f"    {package}")
            else:
                click.echo("  missing packages: none")
            if target.get("unresolved_tools"):
                click.echo("  unresolved tools:")
                for tool in target["unresolved_tools"]:
                    click.echo(f"    {tool}")
        if not target["tools"]:
            click.echo("  - no external tool requirements detected")
            continue
        for tool in target["tools"]:
            plugins = ", ".join(target["plugins"].get(tool, []))
            state = ""
            if tool in set(target.get("missing_tools", [])):
                state = " [missing]"
            elif "present_tools" in target:
                state = " [present]"
            click.echo(f"  {tool}{state}: {plugins}")
        click.echo("  preflight commands:")
        for command in target["commands"]:
            click.echo(f"    {command}")


def _format_csv(values: Iterable[str]) -> str:
    values = list(values)
    return ", ".join(values) if values else "none"


def _echo_capability_install_event(event: Dict[str, Any]) -> None:
    kind = event.get("event")
    if kind == "job":
        click.echo(f"Job: {event['job']}")
        return
    target = event.get("target", "-")
    host = event.get("host", "-")
    os_family = event.get("os", {}).get("family", "unknown")
    if kind == "target-check":
        click.echo(f"[CHECK] {target} {host} os={os_family}: checking required tools")
        return
    if kind == "target-missing":
        missing_tools = event.get("missing_tools", [])
        packages = event.get("packages", [])
        unresolved = event.get("unresolved_tools", [])
        if missing_tools:
            click.echo(f"[MISSING] {target}: tools={_format_csv(missing_tools)}")
        else:
            click.echo(f"[OK] {target}: all required tools already present")
        if packages:
            click.echo(f"[PLAN] {target}: install packages={_format_csv(packages)}")
        if unresolved:
            click.echo(f"[WARN] {target}: unresolved tools={_format_csv(unresolved)}")
        return
    if kind == "target-install":
        click.echo(f"[INSTALL] {target}: packages={_format_csv(event.get('packages', []))}")
        return
    if kind == "target-done":
        status = "OK" if event.get("ok") else "FAILED"
        changed = "changed=true" if event.get("changed") else "changed=false"
        click.echo(f"[{status}] {target} {host} os={os_family} rc={event.get('rc', 0)} {changed}")


def _echo_text_stream(label: str, value: str) -> None:
    click.echo(f"  {label}:")
    previous_blank = False
    for raw_line in value.replace("\r", "\n").splitlines():
        line = raw_line.rstrip()
        if not line:
            if previous_blank:
                continue
            previous_blank = True
        else:
            previous_blank = False
        click.echo(f"    {line}")


def _echo_capability_install_payload(payload: Dict[str, Any], output_format: str, *, verbose: bool = False) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    ok_targets = sum(1 for target in payload["targets"] if target["ok"])
    failed_targets = len(payload["targets"]) - ok_targets
    changed_targets = sum(1 for target in payload["targets"] if target["changed"])
    click.echo("Summary:")
    click.echo(f"  targets: {len(payload['targets'])}")
    click.echo(f"  ok: {ok_targets}")
    click.echo(f"  failed: {failed_targets}")
    click.echo(f"  changed: {changed_targets}")
    suppressed = 0
    for target in payload["targets"]:
        has_output = bool(target["stdout"] or target["stderr"])
        show_output = has_output and (verbose or not target["ok"])
        if has_output and not show_output:
            suppressed += 1
            continue
        if target["stdout"]:
            _echo_text_stream(f"{target['target']} stdout", target["stdout"])
        if target["stderr"]:
            _echo_text_stream(f"{target['target']} stderr", target["stderr"])
    if suppressed:
        click.echo(
            f"Command output suppressed for {suppressed} successful target(s); "
            "use --verbose to show stdout/stderr."
        )


def _echo_os_info_payload(payload: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo("Detected operating-system facts.")
    click.echo("")
    click.echo(f"Inventory: {payload['inventory']}")
    click.echo(f"Targets: {payload['target_count']}")

    summary: dict[str, int] = {}
    for target in payload["targets"]:
        os_info = target["os"]
        pretty = os_info.get("pretty_name") or os_info.get("name") or os_info.get("id") or "unknown"
        version = os_info.get("version_id") or os_info.get("version") or "-"
        codename = os_info.get("version_codename") or "-"
        id_like = ",".join(os_info.get("id_like") or []) or "-"
        user = target.get("user") or "-"
        family = os_info.get("family") or "unknown"
        package_manager = os_info.get("package_manager") or "unknown"
        summary_key = f"{family}/{package_manager}"
        summary[summary_key] = summary.get(summary_key, 0) + 1

        click.echo("")
        click.echo(f"Target {target['target']} {target['host']}:{target['port']}")
        click.echo(f"  user             {user}")
        click.echo(f"  os               {pretty}")
        click.echo(f"  family           {family}")
        click.echo(f"  id               {os_info.get('id') or 'unknown'}")
        click.echo(f"  version          {version}")
        click.echo(f"  codename         {codename}")
        click.echo(f"  id_like          {id_like}")
        click.echo(f"  package manager  {package_manager}")

    if summary:
        click.echo("")
        click.echo("Summary:")
        for key, count in sorted(summary.items()):
            click.echo(f"  {key}: {count} target{'s' if count != 1 else ''}")


def _os_info_payload(
    *,
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    plugin_path: tuple[str, ...],
) -> Dict[str, Any]:
    return _engine(plugin_path).os_info_inventory(
        inventory_path=inventory_path,
        vars_path=vars_path,
        secrets_path=secrets_path,
        limit=_split_selectors(limit),
        exclude=_split_selectors(exclude),
        cli_vars=_parse_vars(cli_vars),
    )


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
@click.option("--verbose", is_flag=True, help="Show per-target substep details in check mode.")
@click.option("--lock", is_flag=True, help="Acquire job/target locks before executing.")
@click.option("--lock-scope", type=click.Choice(["job", "target", "both"]), default="both", show_default=True, help="Lock job, targets or both.")
@click.option("--lock-timeout", type=float, default=0.0, show_default=True, help="Seconds to wait for locks.")
@click.option("--preflight-capabilities", is_flag=True, help="Compatibility flag; capability preflight is implicit for normal runs.")
@click.option("--sudo-password-env", help="Environment variable containing the sudo password for sudo-enabled remote substeps.")
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
    verbose: bool,
    lock: bool,
    lock_scope: str,
    lock_timeout: float,
    preflight_capabilities: bool,
    sudo_password_env: str | None,
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
            _echo_check_payload(payload, output_format, verbose=verbose)
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
            preflight_capabilities=preflight_capabilities,
            sudo_password_env=sudo_password_env,
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
@click.option("--diff", "diff_mode", is_flag=True, help="Render file-oriented diff previews instead of the execution plan.")
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
    diff_mode: bool,
    output_format: str,
) -> None:
    """Print the execution plan without running the job."""
    try:
        engine = _engine(plugin_path)
        if check_mode and diff_mode:
            raise click.ClickException("--check and --diff are mutually exclusive")
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
        if diff_mode:
            payload = engine.diff_job(
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
            _echo_diff_payload(payload, output_format)
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
def ssh() -> None:
    """SSH helper commands."""


@ssh.group("known-hosts")
def known_hosts() -> None:
    """Collect known_hosts entries without trusting them automatically."""


@known_hosts.command("scan")
@click.option("--host", "hosts", multiple=True, help="Host to scan without an inventory file.")
@click.option("--inventory", "inventory_path", type=click.Path(exists=True), help="Inventory YAML path to scan.")
@click.option("--vars", "vars_path", type=click.Path(exists=True), help="External variables YAML path.")
@click.option("--secrets", "secrets_path", type=click.Path(exists=True), help="External secrets YAML path.")
@click.option("--var", "cli_vars", multiple=True, help="Override variable, format KEY=VALUE.")
@click.option("--limit", multiple=True, help="Limit inventory targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude inventory targets. Accepts server, group or group:name.")
@click.option("--port", default=22, show_default=True, type=int, help="SSH port for --host entries.")
@click.option("--timeout", default=5, show_default=True, type=int, help="ssh-keyscan timeout in seconds.")
@click.option("--key-type", "key_types", multiple=True, help="Restrict key type, e.g. ed25519 or rsa.")
@click.option("--output", "output_path", type=click.Path(dir_okay=False), help="Write scanned known_hosts lines to this file.")
@click.option("--append", is_flag=True, help="Append to --output instead of overwriting it.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def scan_known_hosts_command(
    hosts: tuple[str, ...],
    inventory_path: str | None,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    port: int,
    timeout: int,
    key_types: tuple[str, ...],
    output_path: str | None,
    append: bool,
    output_format: str,
) -> None:
    """Scan SSH host keys and print fingerprints for operator verification."""
    try:
        targets = _known_host_targets(
            hosts=hosts,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            cli_vars=_parse_vars(cli_vars),
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            port=port,
        )
        entries = scan_known_hosts(targets, timeout=timeout, key_types=key_types)
        output_exists = Path(output_path).expanduser().exists() if output_path else False
        written = write_known_hosts(entries, output_path, append=append) if output_path else None
    except (AutomaxError, KnownHostsError, InventoryError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc

    payload = {
        "entries": [entry.__dict__ for entry in entries],
        "output": str(written) if written else None,
        "warning": "Verify fingerprints over a trusted channel before using these host keys.",
    }
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    _echo_known_hosts_scan(entries, written=written, append=append, output_exists=output_exists)


def _known_host_key_rank(key_type: str) -> tuple[int, str]:
    ranks = {
        "ssh-ed25519": 0,
        "ecdsa-sha2-nistp256": 1,
        "ecdsa-sha2-nistp384": 1,
        "ecdsa-sha2-nistp521": 1,
        "ssh-rsa": 2,
    }
    return (ranks.get(key_type, 10), key_type)


def _known_host_target_label(entry: KnownHostEntry) -> str:
    endpoint = f"{entry.host}:{entry.port}"
    if entry.target_name == entry.host:
        return f"Target {endpoint}"
    return f"Target {entry.target_name} {endpoint}"


def _echo_known_hosts_scan(
    entries: list[KnownHostEntry],
    *,
    written: Path | None,
    append: bool,
    output_exists: bool,
) -> None:
    click.echo(
        "Scanned SSH host keys. Verify these fingerprints over a trusted channel "
        "before trusting the generated known_hosts file."
    )
    grouped: dict[tuple[str, str, int], list[KnownHostEntry]] = {}
    for entry in entries:
        grouped.setdefault((entry.target_name, entry.host, entry.port), []).append(entry)

    for group_entries in grouped.values():
        click.echo()
        click.echo(_known_host_target_label(group_entries[0]))
        for entry in sorted(group_entries, key=lambda item: _known_host_key_rank(item.key_type)):
            click.echo(f"  {entry.key_type:<20} {entry.fingerprint}")

    if written:
        action = "Appended to" if append else "Overwrote" if output_exists else "Wrote"
        click.echo()
        click.echo(f"{action} known_hosts file: {written}")
    target_count = len(grouped)
    key_count = len(entries)
    target_suffix = "s" if target_count != 1 else ""
    key_suffix = "s" if key_count != 1 else ""
    click.echo(f"Scanned {target_count} target{target_suffix}, {key_count} host key{key_suffix}.")


def _known_host_targets(
    *,
    hosts: tuple[str, ...],
    inventory_path: str | None,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: Dict[str, Any],
    limit: list[str],
    exclude: list[str],
    port: int,
) -> list[Target]:
    if port <= 0:
        raise AutomaxError("known-hosts scan --port must be positive")
    if hosts and inventory_path:
        raise AutomaxError("use either --host or --inventory, not both")
    if not hosts and not inventory_path:
        raise AutomaxError("known-hosts scan requires --host or --inventory")
    if hosts:
        return [Target(name=host, host=host, port=port) for host in hosts]

    engine = _engine(())
    vars_document = load_yaml_file(vars_path, required=False) if vars_path else {}
    secrets_document = load_yaml_file(secrets_path, required=False) if secrets_path else {}
    secrets = engine.secret_manager.resolve_all(secrets_document, base_dir=engine._path_parent(secrets_path))
    variables = engine._merge_variables(vars_document, cli_vars)
    context = {"vars": variables, "secrets": secrets}
    inventory_document = load_inventory_document(inventory_path, context)
    inventory = Inventory(inventory_document, context)
    return inventory.select("all", limit=limit, exclude=exclude)

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
@click.option("--strict", is_flag=True, help="Also reject unknown DSL keys and validate the resolved plan scope.")
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
            use: command.local.run
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
@click.option("--preflight-capabilities", is_flag=True, help="Check remote tools required by the selected job before execution.")
@click.option("--sudo-password-env", help="Environment variable containing the sudo password for sudo-enabled remote substeps.")
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
    preflight_capabilities: bool,
    sudo_password_env: str | None,
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
            sudo_password_env=sudo_password_env,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    sys.exit(rc)


def _echo_manual_commands_payload(payload: Dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo(f"Job: {payload['job']}")
    click.echo("Manual command rendering:")
    if payload.get("sudo_note"):
        click.echo(f"# sudo note: {payload['sudo_note']}")
    for node in payload["nodes"]:
        sudo_marker = "yes" if node.get("uses_sudo") else "no"
        click.echo(f"# target={node['target']} host={node['host']} checkpoint={node['node_id']} plugin={node['plugin']} sudo={sudo_marker}")
        if node["commands"]:
            for command in node["commands"]:
                click.echo(command)
        else:
            click.echo(f"# manual rendering not available: {node.get('reason', 'unknown reason')}")
        click.echo("")


@cli.group()
def commands() -> None:
    """Render manual commands for job recovery."""


@commands.command("render")
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Render commands for substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Skip substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def render_commands(
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
    """Render copy/pasteable commands for selected job substeps."""
    try:
        payload = _engine(plugin_path).manual_commands_job(
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
    _echo_manual_commands_payload(payload, output_format)


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
def os() -> None:
    """Inspect target operating-system facts."""


@os.command("info")
@click.option("--inventory", "inventory_path", required=True, type=click.Path(exists=True), help="External inventory YAML path.")
@click.option("--vars", "vars_path", type=click.Path(exists=True), help="External variables YAML path.")
@click.option("--secrets", "secrets_path", type=click.Path(exists=True), help="External secrets YAML path.")
@click.option("--var", "cli_vars", multiple=True, help="Override variable, format KEY=VALUE.")
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def os_info(
    inventory_path: str,
    vars_path: str | None,
    secrets_path: str | None,
    cli_vars: tuple[str, ...],
    limit: tuple[str, ...],
    exclude: tuple[str, ...],
    plugin_path: tuple[str, ...],
    output_format: str,
) -> None:
    """Detect OS release facts for selected inventory targets."""
    try:
        payload = _os_info_payload(
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            cli_vars=cli_vars,
            limit=limit,
            exclude=exclude,
            plugin_path=plugin_path,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    _echo_os_info_payload(payload, output_format)


@cli.group()
def capabilities() -> None:
    """Inspect job-scoped remote capability requirements."""


@capabilities.command("requirements")
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Show requirements for substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Hide requirements for substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def capability_requirements(
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
    """Render tool requirements derived from the selected job plan."""
    try:
        payload = _engine(plugin_path).capability_requirements_job(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
            check_missing=output_format == "text",
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    _echo_capabilities_payload(payload, output_format)


@capabilities.command("install")
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Install dependencies for substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Skip substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option("--sudo-password-env", help="Environment variable containing the sudo password for package-manager installs.")
@click.option("--verbose", is_flag=True, help="Show successful install command stdout/stderr.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def capability_install(
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
    sudo_password_env: str | None,
    verbose: bool,
    output_format: str,
) -> None:
    """Install missing packages for job-scoped capability requirements."""
    try:
        payload = _engine(plugin_path).install_capability_requirements_job(
            job_path=job_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            secrets_path=secrets_path,
            limit=_split_selectors(limit),
            exclude=_split_selectors(exclude),
            tags=_split_selectors(tags),
            skip_tags=_split_selectors(skip_tags),
            cli_vars=_parse_vars(cli_vars),
            sudo_password_env=sudo_password_env,
            progress_callback=_echo_capability_install_event if output_format == "text" else None,
        )
    except (AutomaxError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    _echo_capability_install_payload(payload, output_format, verbose=verbose)
    if not payload["ok"]:
        raise click.ClickException("one or more targets could not install all missing capability packages")


@cli.group()
def vars() -> None:
    """Inspect job-scoped rendered variables."""


@vars.command("render")
@_apply_common_options
@click.option("--limit", multiple=True, help="Limit targets. Accepts server, group or group:name.")
@click.option("--exclude", multiple=True, help="Exclude targets. Accepts server, group or group:name.")
@click.option("--tags", multiple=True, help="Render context for substeps matching one of these tags.")
@click.option("--skip-tags", multiple=True, help="Skip substeps matching one of these tags.")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def render_vars(
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
    """Render final vars, masked secrets and selected nodes for a job."""
    try:
        payload = _engine(plugin_path).render_vars_job(
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
    _echo_vars_payload(payload, output_format)


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



@plugins.command("audit")
@click.option("--plugin-path", multiple=True, help="External plugin file or directory.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def audit_plugins(plugin_path: tuple[str, ...], output_format: str) -> None:
    """Audit registered plugins for preview, dry-run and manual recovery coverage."""
    payload = audit_plugin_registry(build_builtin_registry(plugin_path))
    if output_format == "json":
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        click.echo("Plugin audit:")
        click.echo(f"  checked:  {payload['checked']}")
        click.echo(f"  failures: {payload['failure_count']}")
        if payload["failures"]:
            click.echo("Failures:")
            for failure in payload["failures"]:
                click.echo(f"  - {failure}")
        click.echo(f"Result: {'OK' if payload['ok'] else 'FAILED'}")
    if not payload["ok"]:
        raise click.exceptions.Exit(1)


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
    schema_document = export_schema(kind)
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            json.dump(schema_document, handle, indent=2, sort_keys=True)
            handle.write("\n")
        click.echo(f"Wrote {output}")
        return
    click.echo(json.dumps(schema_document, indent=2, sort_keys=True) + "\n", nl=False)


def cli_main() -> None:
    """Console-script entry point."""
    cli()


if __name__ == "__main__":
    cli_main()
