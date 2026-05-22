# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Plugin base contract for Automax next engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult


class PluginValidationError(ValueError):
    """Raised when plugin parameters are invalid."""


class BasePlugin(ABC):
    """Stable interface implemented by all action plugins."""

    name = "base"
    aliases: tuple[str, ...] = ()
    description = ""
    category = ""
    required_params: tuple[str, ...] = ()
    optional_params: tuple[str, ...] = ()
    parameter_schema: Dict[str, Dict[str, Any]] = {}
    examples: tuple[str, ...] = ()
    result_fields: Dict[str, str] = {}
    opens_remote_session = False
    supports_dry_run = True
    supports_check_mode = False


    def metadata(self) -> Dict[str, Any]:
        """Return structured metadata used by CLI and documentation generators."""
        parameters = []
        for name in (*self.required_params, *self.optional_params):
            details = dict(self.parameter_schema.get(name, {}))
            parameters.append(
                {
                    "name": name,
                    "required": name in self.required_params,
                    "type": details.get("type", "any"),
                    "default": details.get("default"),
                    "description": details.get("description", ""),
                }
            )
        return {
            "name": self.name,
            "category": self.category or self.name.split(".", 1)[0],
            "description": self.description,
            "required_params": list(self.required_params),
            "optional_params": list(self.optional_params),
            "parameters": parameters,
            "examples": list(self.examples),
            "result_fields": dict(self.result_fields),
            "aliases": list(self.aliases),
            "opens_remote_session": self.opens_remote_session,
            "supports_dry_run": self.supports_dry_run,
            "supports_check_mode": self.supports_check_mode,
        }

    def validate(self, params: Dict[str, Any]) -> None:
        """Validate common required parameters."""
        missing = [key for key in self.required_params if key not in params]
        if missing:
            raise PluginValidationError(
                f"plugin '{self.name}' missing required params: {', '.join(missing)}"
            )

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        """Default dry-run implementation."""
        return PluginResult.success(
            changed=False,
            message=f"dry-run: {self.name}",
            data={"params": params},
        )

    @abstractmethod
    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        """Execute a plugin action."""
