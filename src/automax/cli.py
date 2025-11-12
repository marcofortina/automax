"""
Command-line interface for Automax.

Handles argparse, file locking, and delegates execution to the core main module. Keeps
the CLI lightweight and focused on user interaction.

"""

import argparse
import atexit
import fcntl
import os
import sys
from pathlib import Path

import psutil

from automax.main import run_automax

LOCK_FILE_PATH = Path("/tmp/automax.lock")


def _acquire_lock() -> int:
    """
    Acquire an exclusive lock file to prevent concurrent executions.

    Returns:
        int: File descriptor of the lock file.

    Raises:
        SystemExit: If another instance is already running.

    """
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


def _release_lock(lock_fd: int) -> None:
    """
    Release the lock file and remove it.
    """
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)
    LOCK_FILE_PATH.unlink(missing_ok=True)


def cli_main() -> None:
    """
    Entry point for the CLI.

    Parses arguments and delegates execution to the core orchestrator.

    """
    parser = argparse.ArgumentParser(
        description="Automax - YAML-driven automation framework", prog="automax"
    )
    parser.add_argument(
        "steps", nargs="*", help="Steps/sub-steps to execute (e.g. 1 2:1)"
    )
    parser.add_argument(
        "--config", default="examples/config/config.yaml", help="Path to config YAML"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution")
    parser.add_argument("--json-log", action="store_true", help="Enable JSON logging")
    parser.add_argument("--list", action="store_true", help="List available steps")
    parser.add_argument(
        "--validate-only", action="store_true", help="Validate config only"
    )
    args = parser.parse_args()

    lock_fd = _acquire_lock()
    atexit.register(_release_lock, lock_fd)

    # Delegate to core
    rc = run_automax(
        steps=args.steps,
        config_path=args.config,
        dry_run=args.dry_run,
        json_log=args.json_log,
        list_only=args.list,
        validate_only=args.validate_only,
    )
    sys.exit(rc)


if __name__ == "__main__":
    cli_main()
