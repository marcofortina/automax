# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Plugin base contract for Automax next engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
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
        """Validate the common plugin parameter contract.

        Builtin plugins expose ``required_params``, ``optional_params`` and a
        runtime ``parameter_schema`` populated by the registry metadata pass.
        Keeping this check in the base class makes typos, wrong YAML scalar
        types and unsupported enum values fail before a plugin builds shell
        commands or touches a target.
        """
        if not isinstance(params, Mapping):
            raise PluginValidationError(f"plugin '{self.name}' params must be mapping")

        missing = [key for key in self.required_params if key not in params]
        if missing:
            raise PluginValidationError(
                f"plugin '{self.name}' missing required params: {', '.join(missing)}"
            )

        allowed = set(self.required_params) | set(self.optional_params)
        unknown = sorted(set(params) - allowed)
        if unknown:
            raise PluginValidationError(
                f"plugin '{self.name}' unknown params: {', '.join(unknown)}"
            )

        for name, value in params.items():
            self._validate_parameter(name, value)

    def _validate_parameter(self, name: str, value: Any) -> None:
        """Validate one parameter using this plugin's runtime schema."""
        schema = dict(self.parameter_schema.get(name, {}) or {})
        expected_types = schema.get("types", schema.get("type", "any"))
        if isinstance(expected_types, str):
            expected_types = (expected_types,)
        if expected_types and "any" not in expected_types:
            self._validate_parameter_type(name, value, tuple(str(item) for item in expected_types))

        enum = schema.get("enum")
        if enum is not None and value not in enum:
            allowed = ", ".join(str(item) for item in enum)
            raise PluginValidationError(
                f"plugin '{self.name}' param '{name}' must be one of: {allowed}"
            )

        if "min" in schema and self._is_number(value) and value < schema["min"]:
            raise PluginValidationError(
                f"plugin '{self.name}' param '{name}' must be >= {schema['min']}"
            )
        if "max" in schema and self._is_number(value) and value > schema["max"]:
            raise PluginValidationError(
                f"plugin '{self.name}' param '{name}' must be <= {schema['max']}"
            )
        if schema.get("non_empty") and self._is_empty(value):
            raise PluginValidationError(
                f"plugin '{self.name}' param '{name}' must not be empty"
            )

    def _validate_parameter_type(
        self, name: str, value: Any, expected_types: tuple[str, ...]
    ) -> None:
        known_types = {"string", "path", "boolean", "integer", "number", "list", "sequence", "mapping"}
        if not any(expected_type in known_types for expected_type in expected_types):
            return

        for expected_type in expected_types:
            if expected_type in {"string", "path"} and isinstance(value, str):
                return
            if expected_type == "boolean" and isinstance(value, bool):
                return
            if (
                expected_type == "integer"
                and isinstance(value, int)
                and not isinstance(value, bool)
            ):
                return
            if expected_type == "number" and self._is_number(value):
                return
            if expected_type in {"list", "sequence"} and isinstance(value, list):
                return
            if expected_type == "mapping" and isinstance(value, dict):
                return

        expected = " or ".join(expected_types)
        raise PluginValidationError(
            f"plugin '{self.name}' param '{name}' must be {expected}"
        )

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value is None or value == "" or value == [] or value == {}

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


class ReadOnlyCommandPlugin(BasePlugin):
    """Base class for read-only plugins rendered as shell commands."""

    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return f"{self.name} is a read-only assertion or fact query"

    def command_failure_message(self, params: Dict[str, Any]) -> str:
        """Return the failure message used when the read-only command fails."""
        return f"{self.name} failed"

    def command_result_data(self, params: Dict[str, Any], stdout: str, stderr: str, rc: int) -> Dict[str, Any]:
        """Return optional structured data for a successful command result."""
        return {"output": stdout}

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        commands = self.manual_commands(params, context)
        rc, out, err = self._execute_read_only_commands(commands, context)
        if rc != 0:
            return PluginResult.failure(
                rc=rc,
                stdout=out,
                stderr=err,
                message=self.command_failure_message(params),
            )
        return PluginResult.success(
            changed=False,
            rc=rc,
            stdout=out,
            stderr=err,
            data=self.command_result_data(params, out, err, rc),
        )

    def _execute_read_only_commands(self, commands: list[str], context: ExecutionContext) -> tuple[int, str, str]:
        """Execute one or more read-only commands and aggregate output."""
        from automax.plugins.remote_utils import exec_remote

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        last_rc = 0
        for command in commands:
            last_rc, out, err = exec_remote(context, command)
            if out:
                stdout_parts.append(out)
            if err:
                stderr_parts.append(err)
            if last_rc != 0:
                break
        return last_rc, "\n".join(stdout_parts), "\n".join(stderr_parts)
