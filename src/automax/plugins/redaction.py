# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Secret redaction policy check plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.core.redaction import find_unredacted_secrets, redact_text
from automax.plugins.base import BasePlugin, PluginValidationError


def _payload(params: Dict[str, Any], context: ExecutionContext) -> str:
    if "text" in params:
        return str(params["text"])
    if params.get("source") == "stdout":
        return str(context.outputs.get("stdout", ""))
    if params.get("source") == "stderr":
        return str(context.outputs.get("stderr", ""))
    return str(params.get("value", ""))


class SecretRedactAssertPlugin(BasePlugin):
    name = "security.secret.redact.check"
    description = "Check whether a payload contains no declared secret values after redaction policy is applied."
    optional_params = ("text", "value", "source")
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not any(key in params for key in ("text", "value", "source")):
            raise PluginValidationError("security.secret.redact.check requires text, value or source")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return ["# security.secret.redact.check is evaluated inside Automax before output persistence"]

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "security.secret.redact.check is an in-process redaction policy predicate"

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        text = _payload(params, context)
        leaked = find_unredacted_secrets(text, context.secrets)
        return PluginResult.success(
            changed=False,
            data={
                "clean": not leaked,
                "leaks": len(leaked),
                "redacted": redact_text(text, context.secrets),
            },
        )


class SecretScanOutputPlugin(BasePlugin):
    name = "security.secret.scan_output"
    description = "Scan an arbitrary output payload and report whether redaction would change it."
    optional_params = ("text", "value", "source")
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return ["# security.secret.scan_output is evaluated inside Automax; no shell command is required"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        text = _payload(params, context)
        redacted = redact_text(text, context.secrets)
        return PluginResult.success(changed=False, data={"changed_by_redaction": redacted != text, "redacted": redacted})


class SecretScanPreviewPlugin(SecretScanOutputPlugin):
    name = "security.secret.scan_preview"
    description = "Scan preview/manual-command text with the same redaction policy used by the engine."
