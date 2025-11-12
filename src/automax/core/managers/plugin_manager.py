"""
Plugin manager for the Automax project.

Responsible for dynamically discovering, loading, and managing plugin utilities from the
plugins/ directory. Each plugin must define REGISTER_UTILITIES as a list of (name, func)
tuples, and optionally SCHEMA for validation.

"""

import importlib.util
from pathlib import Path
import sys


class PluginManager:
    """
    Manager class responsible for handling all plugin-related operations.
    """

    def __init__(self, logger=None, plugins_dir: str | Path = "src/automax/plugins"):
        """
        Initialize the PluginManager.

        Args:
            logger (optional): Logger instance for debug/info/error messages.
            plugins_dir (str or Path): Path to the directory containing plugin files.

        """
        self.plugins_dir = Path(plugins_dir).expanduser().resolve()
        self.logger = logger
        self.registry = {}
        self.schemas = {}  # New: Store schemas for validation

    def load_plugins(self):
        """
        Dynamically load plugins from the plugins/ directory and register their
        utilities and schemas.

        Each plugin module must define REGISTER_UTILITIES as a list of (name, func)
        tuples. Optionally defines SCHEMA as a dict for param validation. Logs errors if
        loading fails but continues.

        """
        if not self.plugins_dir.exists():
            if self.logger:
                self.logger.warning(
                    f"Plugins directory not found: {self.plugins_dir}. Skipping plugin loading."
                )
            return

        for plugin_path in self.plugins_dir.glob("*.py"):
            if plugin_path.name.startswith("__"):
                continue

            module_name = f"plugins.{plugin_path.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to load plugin {plugin_path}: {e}")
                continue

            if hasattr(module, "REGISTER_UTILITIES"):
                for name, func in module.REGISTER_UTILITIES:
                    if name in self.registry:
                        raise ValueError(
                            f"Duplicate utility name: {name} from {plugin_path}"
                        )
                    self.registry[name] = func
                    if self.logger:
                        self.logger.debug(
                            f"Registered utility '{name}' from {plugin_path}"
                        )

            if hasattr(module, "SCHEMA"):
                self.schemas[module.REGISTER_UTILITIES[0][0]] = (
                    module.SCHEMA
                )  # Assume first utility name
                if self.logger:
                    self.logger.debug(
                        f"Registered schema for '{module.REGISTER_UTILITIES[0][0]}' from {plugin_path}"
                    )

    def get_plugin(self, name: str):
        """
        Retrieve a registered utility function by name.

        Args:
            name (str): Name of the utility to retrieve

        Returns:
            callable: The utility function

        Raises:
            KeyError: If the utility is not registered

        """
        if name not in self.registry:
            raise KeyError(
                f"Utility '{name}' is not registered in PluginManager registry"
            )
        return self.registry[name]

    def get_schema(self, name: str) -> dict:
        """
        Retrieve the SCHEMA for a plugin utility.

        Args:
            name (str): Utility name.

        Returns:
            dict: Schema dictionary.

        Raises:
            KeyError: If no schema defined.

        """
        if name not in self.schemas:
            raise KeyError(f"No SCHEMA defined for utility '{name}'")
        return self.schemas[name]

    def clear_registry(self):
        """
        Clear the current plugin registry and schemas (useful for testing or reloads).
        """
        self.registry.clear()
        self.schemas.clear()

    def list_plugins(self):
        """
        Return a list of all registered plugin names.
        """
        return list(self.registry.keys())
