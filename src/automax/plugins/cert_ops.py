# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Certificate operation plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


class CertGenerateCsrPlugin(BasePlugin):
    name = "cert.generate_csr"
    description = "Generate a CSR from an existing private key using openssl."
    required_params = ("key", "dest", "subject")
    optional_params = ("config", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "cert.generate_csr creates a CSR artifact; use manual commands for the exact openssl invocation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        config = f" -config {quote(params['config'])}" if params.get("config") else ""
        return [f"{_sudo(params)}openssl req -new -key {quote(params['key'])} -out {quote(params['dest'])} -subj {quote(params['subject'])}{config}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="cert.generate_csr failed")
