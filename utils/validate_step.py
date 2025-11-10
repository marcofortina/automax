#!/usr/bin/env python3
"""
Offline YAML validator for Automax step files.

Validates a specific step YAML against schema, plugins, and config placeholders.
"""

import argparse
import sys
from pathlib import Path

from automax.core.exceptions import AutomaxError
from automax.core.managers.config_manager import ConfigManager
from automax.core.managers.plugin_manager import PluginManager
from automax.core.managers.validation_manager import ValidationManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate an Automax step YAML file against schema and configuration."
    )
    parser.add_argument(
        "--step-file",
        type=Path,
        required=True,
        help="Path to the step YAML file to validate",
    )
    parser.add_argument(
        "--config", type=Path, required=True, help="Path to config YAML"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.step_file.exists():
        print(f"[ERROR] Step file not found: {args.step_file}")
        sys.exit(1)

    if not args.config.exists():
        print(f"[ERROR] Config file not found: {args.config}")
        sys.exit(1)

    # Load config for placeholder resolution
    cfg = ConfigManager(str(args.config)).cfg

    # Determine steps_dir and step_id from path
    steps_dir = args.step_file.parent.parent
    step_id = args.step_file.parent.name.replace("step", "")

    # Load PluginManager
    plugin_mgr = PluginManager()
    plugin_mgr.load_plugins()

    # Initialize ValidationManager
    validator = ValidationManager(
        cfg=cfg, plugin_manager=plugin_mgr, steps_dir=steps_dir
    )

    # Perform validation
    try:
        validator.validate_step_yaml(step_id)
        print(f"[OK] {args.step_file} validated successfully")
        sys.exit(0)
    except AutomaxError as e:
        print(f"[ERROR] {args.step_file} validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
