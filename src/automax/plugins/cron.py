# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Cron management plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file, upload_text_to_temp
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


def _safe_name(name: str) -> str:
    if "/" in name or name in {".", ".."}:
        raise PluginValidationError("cron name must be a simple filename")
    return name


class CronEntryPlugin(BasePlugin):
    name = "cron.entry"
    description = "Manage one /etc/cron.d entry file."
    required_params = ("name", "schedule", "command")
    optional_params = ("user", "state", "env", "sudo")
    parameter_schema = {
        "user": {"type": "string", "default": "root", "description": "User field for /etc/cron.d."},
        "env": {"type": "mapping", "description": "Environment lines written before the cron entry."},
    }
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _safe_name(str(params["name"]))
        if str(params.get("state", "present")) not in {"present", "absent"}:
            raise PluginValidationError("cron.entry state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        dest = f"/etc/cron.d/{params['name']}"
        if str(params.get("state", "present")) == "absent":
            command = f"if test -e {quote(dest)}; then {_sudo(params)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
            rc, out, err = exec_remote(context, command)
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.entry failed")
        env_lines = []
        env = params.get("env") or {}
        if not isinstance(env, dict):
            raise PluginValidationError("cron.entry env must be a mapping")
        for key, value in env.items():
            env_lines.append(f"{key}={value}")
        content = "\n".join(
            [
                "# Managed by Automax",
                *env_lines,
                f"{params['schedule']} {params.get('user', 'root')} {params['command']}",
                "",
            ]
        )
        temp_path = upload_text_to_temp(context, content)
        rc, out, err = install_uploaded_file(context, temp_path, dest, sudo=bool(params.get("sudo", True)), mode="0644", owner="root", group="root")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.entry failed", data={"path": dest})


class CronFilePlugin(BasePlugin):
    name = "cron.file"
    description = "Install or remove a complete /etc/cron.d file."
    required_params = ("name",)
    optional_params = ("content", "state", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _safe_name(str(params["name"]))
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("cron.file state must be present or absent")
        if state == "present" and "content" not in params:
            raise PluginValidationError("cron.file requires content when state=present")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        dest = f"/etc/cron.d/{params['name']}"
        if str(params.get("state", "present")) == "absent":
            command = f"if test -e {quote(dest)}; then {_sudo(params)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
            rc, out, err = exec_remote(context, command)
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.file failed")
        temp_path = upload_text_to_temp(context, str(params["content"]).rstrip() + "\n")
        rc, out, err = install_uploaded_file(context, temp_path, dest, sudo=bool(params.get("sudo", True)), mode="0644", owner="root", group="root")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.file failed", data={"path": dest})
