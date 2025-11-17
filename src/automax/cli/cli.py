"""
Command-line interface for Automax.
"""

import atexit
import fcntl
import os
from pathlib import Path
import sys

import click
import psutil

from automax import __version__
from automax.core.managers.plugin_manager import PluginManager
from automax.main import run_automax

LOCK_FILE_PATH = Path("/tmp/automax.lock")


def _acquire_lock():
    # Acquire an exclusive lock file to prevent concurrent executions.
    if LOCK_FILE_PATH.exists():
        try:
            with open(LOCK_FILE_PATH, "r") as f:
                pid_str = f.read().strip()
                if pid_str and psutil.pid_exists(int(pid_str)):
                    raise SystemExit(
                        "Another instance of Automax is already running. Exiting."
                    )
                os.remove(LOCK_FILE_PATH)
        except (ValueError, psutil.NoSuchProcess):
            os.remove(LOCK_FILE_PATH)

    lock_fd = os.open(LOCK_FILE_PATH, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(lock_fd, str(os.getpid()).encode())
        os.fsync(lock_fd)
    except IOError:
        raise SystemExit("Another instance of Automax is already running. Exiting.")
    return lock_fd


def _release_lock(lock_fd):
    # Release the lock file and remove it.
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)
    LOCK_FILE_PATH.unlink(missing_ok=True)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="Automax")
def cli():
    """Automax - YAML-driven automation framework"""
    pass


@cli.command()
@click.option(
    "--config", help="Path to config YAML", type=click.Path(exists=True), required=True
)
@click.option("--dry-run", is_flag=True, help="Simulate execution")
@click.option(
    "--steps", help="Steps to execute (comma-separated: 1,2,2:1)", required=True
)
@click.option(
    "--var", "variables", multiple=True, help="Set variable in format KEY=VALUE"
)
def run(config, dry_run, steps, variables):
    """
    Execute Automax workflow.
    """
    # Parse steps from comma-separated string
    step_list = steps.split(",") if steps else []

    # Parse variables
    parsed_vars = {}
    for var in variables:
        if "=" not in var:
            click.echo(f"Error: Invalid variable format: {var}")
            click.echo("Use format: KEY=VALUE")
            sys.exit(1)
        key, value = var.split("=", 1)
        parsed_vars[key.strip()] = value.strip()

    click.echo(f"Executing steps: {step_list}")

    # Acquire lock
    lock_fd = _acquire_lock()
    atexit.register(_release_lock, lock_fd)

    # Delegate to core execution
    rc = run_automax(
        steps=step_list,
        config_path=config,
        dry_run=dry_run,
        json_log=False,
        list_only=False,
        validate_only=False,
    )

    sys.exit(rc)


@cli.command()
@click.option(
    "--config", help="Path to config YAML", type=click.Path(exists=True), required=True
)
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
def validate(config, strict):
    """
    Validate Automax workflow file.
    """
    lock_fd = _acquire_lock()
    atexit.register(_release_lock, lock_fd)

    rc = run_automax(
        steps=[],
        config_path=config,
        dry_run=True,
        json_log=False,
        list_only=False,
        validate_only=True,
    )

    sys.exit(rc)


@cli.command()
@click.option(
    "--config", help="Path to config YAML", type=click.Path(exists=True), required=True
)
def list_steps(config):
    """
    List available steps in workflow.
    """
    lock_fd = _acquire_lock()
    atexit.register(_release_lock, lock_fd)

    rc = run_automax(
        steps=[],
        config_path=config,
        dry_run=True,
        json_log=False,
        list_only=True,
        validate_only=False,
    )

    sys.exit(rc)


@cli.group()
def plugins():
    """
    Manage Automax plugins.
    """
    pass


@plugins.command()
def list():
    """
    List available plugins.
    """
    try:
        plugin_manager = PluginManager()
        available_plugins = plugin_manager.list_plugins()

        if available_plugins:
            click.echo("Available plugins:")
            for plugin_name in sorted(available_plugins):
                click.echo(f"  {plugin_name}")
        else:
            click.echo("No plugins found")

    except Exception as e:
        click.echo(f"Error loading plugins: {e}")
        sys.exit(1)


def cli_main():
    """Entry point for CLI - maintains backward compatibility."""
    cli()


if __name__ == "__main__":
    sys.exit(cli_main())
