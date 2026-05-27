# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Service health assertion plugins."""

from __future__ import annotations

import socket
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.http import HttpAssertPlugin
from automax.plugins.remote_utils import exec_remote, quote, sudo_prefix



class HealthPortPlugin(BasePlugin):
    name = "health.port"
    description = "Assert that a TCP port is reachable from the controller or listening on the target."
    required_params = ("port",)
    optional_params = ("host", "listen", "timeout", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "health.port is a read-only assertion with no file diff"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        port = quote(params["port"])
        if bool(params.get("listen", True)):
            return [f"{sudo_prefix(params, default=False)}ss -H -ltn sport = :{port} | grep -q ."]
        host = str(params.get("host", "127.0.0.1"))
        return [f"python3 - <<'PY'\nimport socket\nsocket.create_connection(({host!r}, {int(params['port'])}), timeout={float(params.get('timeout', 3))}).close()\nPY"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if not bool(params.get("listen", True)) and context.ssh_client is None:
            host = str(params.get("host", context.target.host))
            try:
                with socket.create_connection((host, int(params["port"])), timeout=float(params.get("timeout", 3))):
                    return PluginResult.success(message="TCP port reachable", data={"host": host, "port": int(params["port"])})
            except OSError as exc:
                return PluginResult.failure(message=f"TCP port unreachable: {exc}")
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="TCP listen assertion failed")
        return PluginResult.success(stdout=out, stderr=err, data={"port": int(params["port"])})


class HealthListenPlugin(HealthPortPlugin):
    name = "health.listen"
    description = "Assert that a TCP port is listening on the target."


class HealthProcessPlugin(BasePlugin):
    name = "health.process"
    description = "Assert that a remote process matching a pattern exists or is absent."
    required_params = ("pattern",)
    optional_params = ("state", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "health.process is a read-only process assertion with no file diff"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        command = f"pgrep -af -- {quote(params['pattern'])}"
        if str(params.get("state", "present")) == "absent":
            command = f"! {command}"
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="process health assertion failed")
        return PluginResult.success(stdout=out, stderr=err)


class HealthHttpPlugin(HttpAssertPlugin):
    name = "health.http"
    description = "Assert HTTP status and optional body content from the controller."
