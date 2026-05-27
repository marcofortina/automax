# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Log and journal collection plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import exec_remote, quote, sudo_prefix


def _sudo(params: Dict[str, Any]) -> str:
    return sudo_prefix(params, default=False)


def _diff(path: str, text: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": "log-plan", "diff": "".join(unified_diff([], [text + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (query)"))}]


class LogGrepPlugin(BasePlugin):
    name = "log.grep"
    description = "Search remote log files with grep and return matching lines."
    required_params = ("pattern",)
    optional_params = ("files", "max_count", "ignore_missing", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff("log.grep", f"grep pattern={params['pattern']} files={params.get('files', [])}")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        files = params.get("files") or ["/var/log/syslog", "/var/log/messages"]
        if isinstance(files, str):
            files = [files]
        max_count = f" -m {int(params['max_count'])}" if params.get("max_count") else ""
        missing = " -s" if bool(params.get("ignore_missing", True)) else ""
        return [f"{_sudo(params)}grep -R{missing}{max_count} -- {quote(params['pattern'])} {' '.join(quote(item) for item in files)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc not in {0, 1}:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="log.grep failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class JournalCollectPlugin(BasePlugin):
    name = "journal.collect"
    description = "Collect journalctl output for artifact capture through stdout."
    required_params: tuple[str, ...] = ()
    optional_params = ("service", "since", "until", "lines", "output", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _diff("journal.collect", f"journalctl service={params.get('service', '')} since={params.get('since', '')} lines={params.get('lines', '')}")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        command = [f"{_sudo(params)}journalctl", "--no-pager"]
        if params.get("service"):
            command.extend(["-u", quote(params["service"])])
        if params.get("since"):
            command.extend(["--since", quote(params["since"])])
        if params.get("until"):
            command.extend(["--until", quote(params["until"])])
        if params.get("lines"):
            command.extend(["-n", quote(params["lines"])])
        if params.get("output"):
            command.extend(["-o", quote(params["output"])])
        return [" ".join(command)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="journal.collect failed")
        return PluginResult.success(stdout=out, stderr=err)


class JournalGrepPlugin(JournalCollectPlugin):
    name = "journal.grep"
    description = "Collect journalctl output and filter it with grep."
    required_params = ("pattern",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        base = super().manual_commands(params, context)[0]
        return [f"{base} | grep -- {quote(params['pattern'])}"]


class LogExportPlugin(BasePlugin):
    name = "log.export"
    description = "Export remote log or journal output to stdout for declared artifact capture."
    required_params: tuple[str, ...] = ()
    optional_params = ("files", "service", "since", "lines", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "log.export emits stdout for artifact capture and does not modify files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if params.get("files"):
            files = params["files"] if isinstance(params["files"], list) else [params["files"]]
            return [f"{_sudo(params)}tail -n {int(params.get('lines', 200))} {' '.join(quote(item) for item in files)}"]
        return JournalCollectPlugin().manual_commands(params, context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="log.export failed")
        return PluginResult.success(stdout=out, stderr=err)
