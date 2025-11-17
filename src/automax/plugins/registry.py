"""
Plugin registry for dynamic discovery and management.

This module provides centralized plugin registration, discovery, and metadata
management.

"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BasePlugin, PluginMetadata


class PluginRegistry:
    """
    Central registry for plugin registration and discovery.
    """

    def __init__(self):
        self._plugins: Dict[str, Type[BasePlugin]] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        self._loaded = False
        self.logger = logging.getLogger("automax.plugins.registry")

    def register(self, plugin_class: Type[BasePlugin]):
        """
        Register a plugin class in the registry.
        """
        metadata = plugin_class.METADATA
        self._validate_plugin_class(plugin_class, metadata)

        self._plugins[metadata.name] = plugin_class
        self._metadata[metadata.name] = metadata

        self.logger.debug(f"Registered plugin: {metadata.name} v{metadata.version}")

    def _validate_plugin_class(
        self, plugin_class: Type[BasePlugin], metadata: PluginMetadata
    ):
        """
        Validate plugin class before registration.
        """
        if not metadata.name or not isinstance(metadata.name, str):
            raise ValueError(f"Plugin name must be non-empty string: {plugin_class}")

        if (
            metadata.name in self._plugins
            and self._plugins[metadata.name] != plugin_class
        ):
            raise ValueError(f"Plugin name conflict: {metadata.name}")

        if not hasattr(plugin_class, "execute") or not callable(plugin_class.execute):
            raise ValueError(f"Plugin must implement execute method: {metadata.name}")

    def get_plugin_class(self, name: str) -> Type[BasePlugin]:
        """
        Retrieve plugin class by name.
        """
        if name not in self._plugins:
            raise KeyError(f"Plugin not found: {name}")
        return self._plugins[name]

    def get_metadata(self, name: str) -> PluginMetadata:
        """
        Retrieve plugin metadata by name.
        """
        if name not in self._metadata:
            raise KeyError(f"Plugin metadata not found: {name}")
        return self._metadata[name]

    def list_plugins(self, category: Optional[str] = None) -> List[str]:
        """
        List all registered plugins.
        """
        if category:
            return [
                name
                for name, metadata in self._metadata.items()
                if metadata.category == category
            ]
        return list(self._plugins.keys())

    def get_plugins_by_tag(self, tag: str) -> List[str]:
        """
        Find plugins by tag.
        """
        return [
            name for name, metadata in self._metadata.items() if tag in metadata.tags
        ]

    def load_all_plugins(self):
        """
        Discover and load all plugins from the plugins directory.
        """
        if self._loaded:
            return

        plugins_package = "automax.plugins"
        plugins_path = Path(__file__).parent

        for module_file in plugins_path.glob("*.py"):
            if module_file.name in [
                "__init__.py",
                "base.py",
                "exceptions.py",
                "registry.py",
            ]:
                continue

            module_name = module_file.stem
            try:
                self._load_plugin_module(plugins_package, module_name)
            except Exception as e:
                self.logger.warning(f"Failed to load plugin module {module_name}: {e}")

        self._loaded = True
        self.logger.info(f"Loaded {len(self._plugins)} plugins")

    def _load_plugin_module(self, package: str, module_name: str):
        """
        Load and register plugins from a module.
        """
        try:
            full_module_name = f"{package}.{module_name}"
            module = importlib.import_module(full_module_name)

            # Find all classes in the module that are BasePlugin subclasses
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    obj.__module__ == module.__name__
                    and issubclass(obj, BasePlugin)
                    and obj is not BasePlugin
                ):

                    self.register(obj)
                    self.logger.debug(f"Discovered plugin: {obj.METADATA.name}")

        except Exception as e:
            self.logger.error(f"Error loading module {module_name}: {e}")
            raise


# Global plugin registry instance
global_registry = PluginRegistry()


def register_plugin(plugin_class: Type[BasePlugin]) -> Type[BasePlugin]:
    """
    Class decorator for automatic plugin registration.
    """
    global_registry.register(plugin_class)
    return plugin_class
