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
    required_params: tuple[str, ...] = ()
    optional_params: tuple[str, ...] = ()
    opens_remote_session = False
    supports_dry_run = True
    supports_check_mode = False

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
