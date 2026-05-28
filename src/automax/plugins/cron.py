# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Cron management plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, ReadOnlyCommandPlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file, upload_text_to_temp
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_stdin, quote, result_from_remote, sudo_prefix, validate_env_name



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
        env = params.get("env") or {}
        if not isinstance(env, dict):
            raise PluginValidationError("cron.entry env must be a mapping")
        for key, value in env.items():
            validate_env_name(key)
            if "\n" in str(value) or "\r" in str(value):
                raise PluginValidationError("cron.entry env values must be single-line")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        dest = f"/etc/cron.d/{params['name']}"
        if str(params.get("state", "present")) == "absent":
            command = f"if test -e {quote(dest)}; then {sudo_prefix(params, default=True)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
            rc, out, err = exec_remote(context, command)
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.entry failed")
        env_lines = []
        env = params.get("env") or {}
        for key, value in env.items():
            env_lines.append(f"{validate_env_name(key)}={value}")
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
            command = f"if test -e {quote(dest)}; then {sudo_prefix(params, default=True)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
            rc, out, err = exec_remote(context, command)
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.file failed")
        temp_path = upload_text_to_temp(context, str(params["content"]).rstrip() + "\n")
        rc, out, err = install_uploaded_file(context, temp_path, dest, sudo=bool(params.get("sudo", True)), mode="0644", owner="root", group="root")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.file failed", data={"path": dest})


class CronListPlugin(ReadOnlyCommandPlugin):
    name = "cron.list"
    description = "List system cron.d entries and optionally one user's crontab."
    optional_params = ("user", "sudo")
    parameter_schema = {"user": {"type": "string", "description": "User account whose crontab should be listed."}}
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "cron.list is a read-only cron listing"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if params.get("user"):
            return [f"{sudo_prefix(params, default=True)}crontab -l -u {quote(params['user'])}"]
        return [f"{sudo_prefix(params, default=True)}ls -1 /etc/cron.d 2>/dev/null || true; {sudo_prefix(params, default=True)}crontab -l 2>/dev/null || true"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="cron.list failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"cron": out})


class CronAbsentPlugin(BasePlugin):
    name = "cron.absent"
    description = "Remove one /etc/cron.d entry file."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _safe_name(str(params["name"]))

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "cron.absent removes one /etc/cron.d file when present"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = f"/etc/cron.d/{params['name']}"
        return [f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}rm -f {quote(path)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="cron.absent failed")


class CronValidatePlugin(ReadOnlyCommandPlugin):
    name = "cron.validate"
    description = "Validate basic cron file syntax without installing it."
    required_params = ("path",)
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        script = r'''
set -eu
file=$1
awk '
  /^[[:space:]]*($|#)/ { next }
  /^[A-Za-z_][A-Za-z0-9_]*=/ { next }
  NF < 6 { printf "invalid cron line %d: %s\n", NR, $0 > "/dev/stderr"; bad=1 }
  END { exit bad ? 1 : 0 }
' "$file"
'''
        return [
            heredoc_to_stdin(
                f"{sudo_prefix(params, default=True)}sh -s -- {quote(params['path'])}",
                script,
                prefix="AUTOMAX_SH",
            )
        ]
