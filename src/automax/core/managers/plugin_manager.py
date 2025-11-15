"""
Plugin Manager for Automax.

This module handles plugin loading, registration, and execution.

"""

from typing import Any, Dict, List

from automax.plugins.exceptions import PluginError, PluginExecutionError
from automax.plugins.registry import global_registry


class PluginManager:
    """
    Manages plugin loading and execution.

    This class provides backward compatibility with the existing system while
    integrating with the new plugin registry.

    """

    def __init__(self, logger=None):
        """
        Initialize the PluginManager.

        Args:
            logger (optional): Logger instance for debug/info/error messages.

        """
        self.logger = logger
        self._legacy_plugins: Dict[str, Any] = {}
        self._load_legacy_plugins()

    def _load_legacy_plugins(self):
        """
        Load plugins using legacy method for backward compatibility.
        """
        import importlib
        from pathlib import Path

        if self.logger:
            self.logger.debug("Loading legacy plugins...")

        plugins_dir = Path(__file__).parent.parent.parent / "plugins"

        for module_file in plugins_dir.glob("*.py"):
            if module_file.name in [
                "__init__.py",
                "base.py",
                "exceptions.py",
                "registry.py",
            ]:
                continue

            module_name = module_file.stem
            try:
                module = importlib.import_module(f"automax.plugins.{module_name}")

                # Look for legacy plugin functions
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and not attr_name.startswith("_"):
                        self._legacy_plugins[module_name] = attr
                        break

            except Exception as e:
                self.logger.warning(f"Failed to load legacy plugin {module_name}: {e}")

    def execute_plugin(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin with given configuration.

        This method first tries the new registry system, then falls back to legacy
        plugins for backward compatibility.

        """
        if self.logger:
            self.logger.debug(f"Executing plugin {name} with configuration {config}")

        # Try new registry system first
        global_registry.load_all_plugins()

        if name in global_registry.list_plugins():
            try:
                plugin_class = global_registry.get_plugin_class(name)
                plugin_instance = plugin_class(config)
                return plugin_instance.execute()
            except Exception as e:
                raise PluginExecutionError(
                    f"Plugin {name} execution failed: {e}"
                ) from e

        # Fall back to legacy system
        elif name in self._legacy_plugins:
            self.logger.warning(f"Using legacy plugin: {name}")
            try:
                return self._legacy_plugins[name](config)
            except Exception as e:
                raise PluginExecutionError(
                    f"Legacy plugin {name} execution failed: {e}"
                ) from e

        else:
            available_plugins = global_registry.list_plugins() + list(
                self._legacy_plugins.keys()
            )
            raise PluginError(
                f"Plugin '{name}' not found. Available plugins: {available_plugins}"
            )

    def get_plugin(self, plugin_name: str):
        """
        Get plugin class by name.
        """
        return global_registry.get_plugin_class(plugin_name)

    def list_plugins(self) -> List[str]:
        """
        List all available plugins.
        """
        global_registry.load_all_plugins()
        new_plugins = global_registry.list_plugins()
        legacy_plugins = list(self._legacy_plugins.keys())

        # Remove duplicates, preferring new system
        all_plugins = list(dict.fromkeys(new_plugins + legacy_plugins))
        return all_plugins


# Global plugin manager instance for backward compatibility
_plugin_manager_instance = None


def get_plugin_manager() -> PluginManager:
    """
    Get the global plugin manager instance.
    """
    global _plugin_manager_instance
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager()
    return _plugin_manager_instance
