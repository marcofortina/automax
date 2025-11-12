#!/usr/bin/env python3
"""
Offline config checker for Automax.

Validates config YAML structure and required keys.

"""

import argparse
from pathlib import Path

import yaml

from automax.core.exceptions import AutomaxError


def parse_args():
    parser = argparse.ArgumentParser(description="Validate Automax config YAML offline")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        return

    try:
        cfg = yaml.safe_load(config_path.read_text())
        required_keys = ["ssh", "log_dir", "log_level", "steps_dir"]
        for key in required_keys:
            if key not in cfg:
                raise AutomaxError(f"Missing required key in config: {key}")
        print(f"[INFO] Config {config_path} is valid")
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML parsing error: {e}")
    except AutomaxError as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
