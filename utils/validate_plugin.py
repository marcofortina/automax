#!/usr/bin/env python3
"""
Plugin validation utility for Automax developers.

Validates a single plugin by name to ensure it meets the class-based plugin
requirements.

"""

import argparse
import importlib.util
from pathlib import Path
import sys

from automax.plugins.base import BasePlugin


def parse_args():
    parser = argparse.ArgumentParser(description="Validate a single Automax plugin")
    parser.add_argument(
        "--plugin",
        required=True,
        help="Path to the plugin file to validate (e.g., src/automax/plugins/local_command.py)",
    )
    return parser.parse_args()


def load_plugin_class_from_file(file_path):
    """
    Load a plugin class directly from a Python file.
    """
    file_path = Path(file_path)

    # Derive module name from file path
    module_name = file_path.stem

    # Load the module from file
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Could not load spec from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Find the plugin class in the module
    plugin_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, BasePlugin)
            and attr is not BasePlugin
            and hasattr(attr, "execute")
            and hasattr(attr, "METADATA")
        ):
            plugin_class = attr
            break

    if plugin_class is None:
        raise ValueError(f"No valid plugin class found in {file_path}")

    return plugin_class, module_name


def validate_plugin_class(plugin_class, plugin_name):
    """
    Validate a single plugin class against the required structure.
    """
    errors = []
    warnings = []

    print(f"🔍 Validating plugin: {plugin_name}")
    print(f"   Class: {plugin_class.__name__}")

    # Required: execute method
    if not hasattr(plugin_class, "execute"):
        errors.append("Missing 'execute' method")
    else:
        print("   ✅ execute method present")

    # Check for METADATA
    if hasattr(plugin_class, "METADATA"):
        print("   ✅ METADATA present")
        metadata = plugin_class.METADATA

        # Check required metadata fields
        required_metadata = ["name", "version", "description"]
        for field in required_metadata:
            if hasattr(metadata, field) and getattr(metadata, field):
                print(f"   ✅ {field}: {getattr(metadata, field)}")
            else:
                errors.append(f"METADATA missing required field: {field}")

        # Check optional metadata fields
        optional_metadata = [
            "author",
            "category",
            "tags",
            "required_config",
            "optional_config",
        ]
        for field in optional_metadata:
            if hasattr(metadata, field):
                value = getattr(metadata, field)
                print(f"   ✅ {field}: {value}")
            else:
                warnings.append(f"METADATA missing optional field: {field}")
    else:
        errors.append("Missing 'METADATA'")

    # Check for SCHEMA
    if hasattr(plugin_class, "SCHEMA"):
        schema = plugin_class.SCHEMA
        if not isinstance(schema, dict):
            errors.append("SCHEMA must be a dictionary")
        else:
            print(f"   ✅ SCHEMA present with {len(schema)} fields")
            # Validate schema structure
            for field, config in schema.items():
                if not isinstance(config, dict):
                    errors.append(f"SCHEMA field '{field}' must be a dictionary")
                elif "type" not in config:
                    errors.append(f"SCHEMA field '{field}' missing 'type'")
                elif "required" not in config:
                    errors.append(f"SCHEMA field '{field}' missing 'required'")
                else:
                    print(
                        f"   ✅ SCHEMA field '{field}': type={config['type']}, required={config['required']}"
                    )
    else:
        errors.append("Missing 'SCHEMA' for parameter validation")

    # Check class docstring
    if not plugin_class.__doc__:
        warnings.append("Plugin class missing docstring")
    else:
        print("   ✅ Plugin has docstring")

    # Check if plugin inherits from BasePlugin
    if not issubclass(plugin_class, BasePlugin):
        errors.append("Plugin does not inherit from BasePlugin")
    else:
        print("   ✅ Inherits from BasePlugin")

    # Check execute method docstring
    execute_method = getattr(plugin_class, "execute")
    if not execute_method.__doc__:
        warnings.append("execute method missing docstring")
    else:
        print("   ✅ execute method has docstring")

    return errors, warnings


def main():
    args = parse_args()

    # Load plugin directly from file
    try:
        plugin_class, plugin_name = load_plugin_class_from_file(args.plugin)
        print(f"📦 Successfully loaded plugin from: {args.plugin}")
    except Exception as e:
        print(f"❌ Failed to load plugin from {args.plugin}: {e}")
        sys.exit(1)

    # Validate the plugin class
    errors, warnings = validate_plugin_class(plugin_class, plugin_name)

    # Report results
    print("\n" + "=" * 50)

    if warnings:
        print(f"⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")

    if errors:
        print(f"❌ Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    else:
        print("✅ Plugin validation passed!")
        if warnings:
            print("   Note: There are warnings but the plugin is functional")
        sys.exit(0)


if __name__ == "__main__":
    main()
