# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Plugin base contract for Automax next engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.validation import PluginValidationError


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
        """Default dry-run implementation with operator preview data."""
        from automax.plugins.manual_preview import fallback_dry_run_data

        return PluginResult.success(
            changed=False,
            message=f"dry-run: {self.name}",
            data=fallback_dry_run_data(self.name, params, context),
        )

    def diff_preview(
        self, params: Dict[str, Any], context: ExecutionContext
    ) -> list[Dict[str, Any]]:
        """Return safe previews for plugins without a dedicated file diff renderer."""
        from automax.plugins.manual_preview import fallback_diff_preview

        return fallback_diff_preview(self.name, params, context)

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        """Explain that the generic preview is an operation plan, not a file diff."""
        return f"{self.name} uses a generic operation-plan preview because it has no deterministic file diff"

    def manual_commands(
        self, params: Dict[str, Any], context: ExecutionContext
    ) -> list[str]:
        """Return copy/pasteable shell commands for manual recovery."""
        from automax.plugins.manual_preview import fallback_manual_commands

        return fallback_manual_commands(self.name, params, context)

    def manual_commands_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        """Explain whether a dedicated or generic manual renderer is used."""
        return f"{self.name} uses the generic legacy manual command renderer"

    @abstractmethod
    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        """Execute a plugin action."""
