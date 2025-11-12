"""
Manager subpackage for Automax.

Includes:
- ConfigManager
- LoggerManager
- PluginManager

"""

from .config_manager import ConfigManager
from .logger_manager import LoggerManager
from .plugin_manager import PluginManager

__all__ = ["ConfigManager", "LoggerManager", "PluginManager"]
