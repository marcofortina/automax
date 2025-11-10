#!/usr/bin/env python3
"""
Offline dry-run validator for steps using programmatic API.
"""

import argparse

from automax import run_automax


def parse_args():
    parser = argparse.ArgumentParser(description="Dry-run validate steps offline")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    parser.add_argument(
        "--steps", nargs="+", required=True, help="Step IDs to validate"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rc = run_automax(
        steps=args.steps, config_path=args.config, dry_run=True, validate_only=True
    )
    print(f"[INFO] Dry-run completed with exit code {rc}")


if __name__ == "__main__":
    main()
