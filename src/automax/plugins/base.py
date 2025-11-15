"""
Base classes and interfaces for Automax plugins.

This module defines the abstract base class and metadata structure that all plugins must
implement.

"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List

from .exceptions import PluginConfigurationError


class PluginMetadata:
    """
    Standardized metadata for plugin registration and discovery.

    Attributes:
        name: Unique identifier for the plugin
        version: Semantic version of the plugin
        description: Brief description of plugin functionality
        author: Plugin author or maintainer
        category: Functional category for grouping
        tags: Keywords for search and filtering
        required_config: List of required configuration keys
        optional_config: List of optional configuration keys

    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        author: str = "Automax",
        category: str = "general",
        tags: List[str] = None,
        required_config: List[str] = None,
        optional_config: List[str] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.category = category
        self.tags = tags or []
        self.required_config = required_config or []
        self.optional_config = optional_config or []


class BasePlugin(ABC):
    """
    Abstract base class defining the plugin interface.

    All Automax plugins must inherit from this class and implement the required abstract
    methods.

    """

    METADATA = PluginMetadata(name="base")

    # Schema for parameter validation - can be overridden by subclasses
    SCHEMA = {}

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize plugin with configuration.

        Args:
            config: Plugin configuration dictionary

        Raises:
            PluginConfigurationError: If required configuration is missing

        """
        self.config = config
        self.logger = self._setup_logger()
        self._validate_config()

    def _setup_logger(self) -> logging.Logger:
        """
        Configure standardized logger for plugin.

        Returns:
            Configured logger instance

        """
        logger_name = f"automax.plugins.{self.METADATA.name}"
        return logging.getLogger(logger_name)

    def _validate_config(self):
        """
        Validate plugin configuration against required fields.

        Raises:
            PluginConfigurationError: If required configuration keys are missing

        """
        missing_required = [
            key for key in self.METADATA.required_config if key not in self.config
        ]

        if missing_required:
            raise PluginConfigurationError(
                f"Missing required configuration: {missing_required}"
            )

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the plugin's main functionality.

        Returns:
            Dictionary containing execution results

        """
        pass

    def validate(self) -> bool:
        """
        Validate plugin readiness before execution.

        Returns:
            True if plugin is ready for execution

        """
        return True

    def cleanup(self):
        """
        Release resources and perform cleanup operations.
        """
        pass

    def get_help(self) -> str:
        """
        Get usage documentation for the plugin.

        Returns:
            Help text describing plugin usage and configuration

        """
        return self.METADATA.description

    def get_example_config(self) -> Dict[str, Any]:
        """
        Generate example configuration for the plugin.

        Returns:
            Example configuration dictionary

        """
        example = {}
        for key in self.METADATA.required_config:
            example[key] = f"<{key}>"
        for key in self.METADATA.optional_config:
            example[key] = f"[{key}]"
        return example
