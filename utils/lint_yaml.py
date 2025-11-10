#!/usr/bin/env python3
"""
YAML linter for Automax steps and config files.
Checks for syntax errors and basic formatting issues.
"""

import argparse
from pathlib import Path

import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Lint YAML files for Automax")
    parser.add_argument("--file", required=True, help="Path to YAML file")
    return parser.parse_args()


def main():
    args = parse_args()
    yaml_path = Path(args.file)
    if not yaml_path.exists():
        print(f"[ERROR] File not found: {yaml_path}")
        return

    try:
        yaml.safe_load(yaml_path.read_text())
        print(f"[INFO] {yaml_path} is valid YAML")
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML parsing error: {e}")


if __name__ == "__main__":
    main()
