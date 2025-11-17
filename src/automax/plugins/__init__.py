"""
Plugin package for Automax.

This package contains all plugin implementations and provides the plugin registration
and discovery system.

"""

from .base import BasePlugin, PluginMetadata
from .exceptions import (
    PluginConfigurationError,
    PluginError,
    PluginExecutionError,
    PluginSecurityError,
    PluginValidationError,
    handle_plugin_errors,
)
from .registry import PluginRegistry, global_registry, register_plugin

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginError",
    "PluginConfigurationError",
    "PluginExecutionError",
    "PluginValidationError",
    "PluginSecurityError",
    "handle_plugin_errors",
    "PluginRegistry",
    "global_registry",
    "register_plugin",
]
