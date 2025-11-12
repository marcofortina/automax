"""
Offline Step Dependency Checker for Automax.

Scans all step directories and validates that:
- YAML file exists for each step
- All sub-step plugins exist in the plugins registry
- Config placeholders in params are resolvable (optional)

"""

import argparse
from pathlib import Path
import sys

from automax.core.exceptions import AutomaxError
from automax.core.managers.plugin_manager import PluginManager
from automax.core.managers.validation_manager import ValidationManager


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Check step dependencies in Automax offline."
    )
    parser.add_argument(
        "--steps-dir", required=True, help="Directory containing step folders"
    )
    parser.add_argument("--config", required=True, help="Path to config YAML")
    return parser.parse_args()


def main():
    args = parse_args()
    steps_dir = Path(args.steps_dir)
    config_path = Path(args.config)

    if not steps_dir.exists() or not steps_dir.is_dir():
        print(f"[ERROR] Steps directory not found or not a directory: {steps_dir}")
        sys.exit(1)
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    # Load config
    try:
        import yaml

        with open(config_path) as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load config YAML: {e}")
        sys.exit(1)

    # Initialize PluginManager and load plugins
    pm = PluginManager()
    pm.load_plugins()

    # Initialize ValidationManager
    vm = ValidationManager(cfg, plugin_manager=pm, steps_dir=steps_dir)

    errors = 0

    # Scan steps directories
    for step_path in steps_dir.iterdir():
        if not step_path.is_dir():
            continue  # skip files
        if not step_path.name.startswith("step"):
            continue  # skip non-step dirs like __pycache__

        yaml_file = step_path / f"{step_path.name}.yaml"
        if not yaml_file.exists():
            print(f"[ERROR] Missing YAML for step: {yaml_file}")
            errors += 1
            continue

        # Validate YAML with ValidationManager
        try:
            vm.validate_step_yaml(step_path.name.replace("step", ""))
            print(f"[OK] Step validated: {yaml_file}")
        except AutomaxError as e:
            print(f"[ERROR] {yaml_file} validation failed: {e}")
            errors += 1

    print(f"\nValidation finished with {errors} error(s).")
    sys.exit(errors)


if __name__ == "__main__":
    main()
