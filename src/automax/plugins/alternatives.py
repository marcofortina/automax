# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Alternatives management plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix


def _sudo(params: Dict[str, Any]) -> str:
    return sudo_prefix(params, default=True)


class AlternativesSetPlugin(BasePlugin):
    name = "alternatives.set"
    description = "Set a system alternative using update-alternatives or alternatives."
    required_params = ("name", "path")
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        diff = "".join(unified_diff([], [f"{params['name']} -> {params['path']}\n"], fromfile="alternative (current)", tofile="alternative (desired)"))
        return [{"path": f"alternative:{params['name']}", "kind": "alternative-plan", "diff": diff}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        return [f"if command -v update-alternatives >/dev/null 2>&1; then {sudo}update-alternatives --set {quote(params['name'])} {quote(params['path'])}; elif command -v alternatives >/dev/null 2>&1; then {sudo}alternatives --set {quote(params['name'])} {quote(params['path'])}; else echo 'no alternatives command found' >&2; exit 1; fi"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="alternatives.set failed")


class AlternativesGetPlugin(BasePlugin):
    name = "alternatives.get"
    description = "Read the current alternatives configuration for one alternative name."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "alternatives.get is a read-only alternatives query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = _sudo(params)
        name = quote(params["name"])
        return [f"if command -v update-alternatives >/dev/null 2>&1; then {sudo}update-alternatives --query {name}; elif command -v alternatives >/dev/null 2>&1; then {sudo}alternatives --display {name}; else echo 'no alternatives command found' >&2; exit 1; fi"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="alternatives.get failed", data={"name": str(params["name"])})


class AlternativesListPlugin(BasePlugin):
    name = "alternatives.list"
    description = "List known system alternatives across update-alternatives or alternatives implementations."
    required_params = ()
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "alternatives.list is a read-only alternatives inventory query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = _sudo(params)
        return [
            "if command -v update-alternatives >/dev/null 2>&1; then "
            f"{sudo}update-alternatives --get-selections; "
            "elif command -v alternatives >/dev/null 2>&1; then "
            "for path in /var/lib/alternatives/* /var/lib/dpkg/alternatives/*; do [ -f \"$path\" ] && basename \"$path\"; done | sort -u; "
            "else echo 'no alternatives command found' >&2; exit 1; fi"
        ]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        names = [line.split()[0] for line in out.splitlines() if line.strip()] if rc == 0 else []
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="alternatives.list failed", data={"names": names})
