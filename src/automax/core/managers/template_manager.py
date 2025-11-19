"""
Template management utilities for Automax using Jinja2.

Provides centralized template rendering with context management and support for custom
filters and functions.

"""

import os
from typing import Any, Dict

from jinja2 import BaseLoader, Environment, StrictUndefined

from automax.core.exceptions import AutomaxError


class TemplateManager:
    """
    Manages Jinja2 template rendering with Automax context.

    Provides consistent template rendering across different components with access to
    config, context, and environment variables.

    """

    def __init__(self, config: Dict[str, Any], context: Dict[str, Any] = None):
        """
        Initialize TemplateManager.

        Args:
            config: Configuration dictionary
            context: Step execution context (optional)

        """
        self.config = config
        self.context = context or {}
        self._environment = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_custom_filters()

    def _register_custom_filters(self):
        """
        Register custom Jinja2 filters.
        """
        # Example custom filters - can be extended
        self._environment.filters["to_yaml"] = self._to_yaml_filter
        self._environment.filters["to_json"] = self._to_json_filter

    def _to_yaml_filter(self, value):
        """
        Convert value to YAML string (placeholder for future implementation).
        """
        # TODO: Implement YAML conversion
        return str(value)

    def _to_json_filter(self, value):
        """
        Convert value to JSON string (placeholder for future implementation).
        """
        # TODO: Implement JSON conversion
        return str(value)

    def render(self, template_string: str, extra_context: Dict[str, Any] = None) -> str:
        """
        Render a template string with Automax context.

        Args:
            template_string: The template string to render
            extra_context: Additional context variables (optional)

        Returns:
            Rendered string

        Raises:
            AutomaxError: If template rendering fails

        """
        try:
            template = self._environment.from_string(template_string)

            # Build complete context - enable dot notation for dict access
            context = {
                "config": DotDict(self.config),
                "context": DotDict(self.context),
                "env": DotDict(dict(os.environ)),
            }

            if extra_context:
                # Convert extra_context dicts to DotDict as well
                converted_extra = {}
                for key, value in extra_context.items():
                    if isinstance(value, dict):
                        converted_extra[key] = DotDict(value)
                    else:
                        converted_extra[key] = value
                context.update(converted_extra)

            return template.render(**context)

        except Exception as e:
            raise AutomaxError(f"Template rendering failed: {str(e)}")

    def render_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively render all string values in a dictionary.

        Args:
            data: Dictionary with potential template strings

        Returns:
            Dictionary with rendered values

        """
        rendered = {}
        for key, value in data.items():
            if isinstance(value, str):
                rendered[key] = self.render(value)
            elif isinstance(value, dict):
                rendered[key] = self.render_dict(value)
            elif isinstance(value, list):
                rendered[key] = [
                    (
                        self.render_dict(item)
                        if isinstance(item, dict)
                        else self.render(item) if isinstance(item, str) else item
                    )
                    for item in value
                ]
            else:
                rendered[key] = value
        return rendered


class DotDict:
    """
    A dictionary that allows dot notation access to attributes.

    This enables Jinja2 templates to use dot notation for dictionary access.
    Example: {{ config.temp_dir }} instead of {{ config['temp_dir'] }}

    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize DotDict with a dictionary.
        """
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, DotDict(value))
            else:
                setattr(self, key, value)

    def __getitem__(self, key):
        """
        Allow bracket notation for backward compatibility.
        """
        return getattr(self, key)

    def __getattr__(self, key):
        """
        Return None for missing attributes to prevent Jinja2 errors.

        This allows templates to safely reference potentially missing variables.

        """
        return None

    def get(self, key, default=None):
        """
        Implement get method similar to dict.get().
        """
        return getattr(self, key, default)

    def __contains__(self, key):
        """
        Check if key exists.
        """
        return hasattr(self, key)

    def __repr__(self):
        """
        String representation of DotDict.
        """
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return f"DotDict({attrs})"
