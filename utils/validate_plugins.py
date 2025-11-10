#!/usr/bin/env python3
"""
Offline plugin validation for Automax.
Checks that all plugins in the plugins directory can be loaded
and have proper SCHEMA defined.
"""

import argparse
from pathlib import Path

from automax.core.managers.plugin_manager import PluginManager


def parse_args():
    parser = argparse.ArgumentParser(description="Validate Automax plugins offline")
    parser.add_argument(
        "--plugins-dir", required=True, help="Path to plugins directory"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    plugins_dir = Path(args.plugins_dir)
    pm = PluginManager(plugins_dir=plugins_dir)
    pm.load_plugins()

    print(f"[INFO] Plugins loaded from {plugins_dir}")
    print(f"[INFO] Registered utilities: {pm.list_plugins()}")


if __name__ == "__main__":
    main()
