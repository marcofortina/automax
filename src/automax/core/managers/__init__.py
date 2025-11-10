"""
Manager subpackage for Automax.

Includes:
- ConfigManager
- LoggerManager
"""

from .config_manager import ConfigManager
from .logger_manager import LoggerManager

__all__ = ["ConfigManager", "LoggerManager"]
