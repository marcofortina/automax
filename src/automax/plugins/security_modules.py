# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SELinux and AppArmor management plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix


def _sudo(params: Dict[str, Any]) -> str:
    return sudo_prefix(params, default=True)


class SelinuxModePlugin(BasePlugin):
    name = "selinux.mode"
    description = "Set SELinux runtime and/or persistent mode."
    required_params = ("state",)
    optional_params = ("persist", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if str(params["state"]) not in {"enforcing", "permissive", "disabled"}:
            raise PluginValidationError("selinux.mode state must be enforcing, permissive or disabled")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params["state"])
        persist = bool(params.get("persist", False))
        script = r'''
set -eu
state=$1
persist=$2
changed=0
if command -v getenforce >/dev/null 2>&1 && [ "$state" != disabled ]; then
  current=$(getenforce | tr '[:upper:]' '[:lower:]')
  if [ "$current" != "$state" ]; then
    if [ "$state" = enforcing ]; then setenforce 1; else setenforce 0; fi
    changed=1
  fi
fi
if [ "$persist" = true ] && [ -e /etc/selinux/config ]; then
  upper=$(printf '%s' "$state" | tr '[:lower:]' '[:upper:]')
  tmp=$(mktemp)
  awk -v val="$upper" 'BEGIN{done=0} /^SELINUX=/ {print "SELINUX=" val; done=1; next} {print} END{if(!done) print "SELINUX=" val}' /etc/selinux/config > "$tmp"
  if ! cmp -s "$tmp" /etc/selinux/config; then
    cat "$tmp" > /etc/selinux/config
    changed=1
  fi
  rm -f "$tmp"
fi
if [ "$changed" = 1 ]; then echo __AUTOMAX_CHANGED__; fi
'''
        command = f"{_sudo(params)}sh -s -- {quote(state)} {quote(str(persist).lower())} <<'SH'\n{script}\nSH"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="selinux.mode failed")


class SelinuxBooleanPlugin(BasePlugin):
    name = "selinux.boolean"
    description = "Set an SELinux boolean."
    required_params = ("name", "value")
    optional_params = ("persist", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        value = "on" if bool(params["value"]) or str(params["value"]).lower() in {"1", "true", "on", "yes"} else "off"
        flag = "-P" if bool(params.get("persist", True)) else ""
        command = (
            f"current=$(getsebool {quote(params['name'])} 2>/dev/null | awk '{{print $3}}' || true); "
            f"if [ \"$current\" = {quote(value)} ]; then true; "
            f"else {_sudo(params)}setsebool {flag} {quote(params['name'])} {quote(value)} && echo {CHANGE_MARKER}; fi"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="selinux.boolean failed")


class SelinuxContextPlugin(BasePlugin):
    name = "selinux.context"
    description = "Manage an SELinux fcontext rule."
    required_params = ("path", "selinux_type")
    optional_params = ("state", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("selinux.context state must be present or absent")
        if state == "present":
            command = f"{_sudo(params)}semanage fcontext -a -t {quote(params['selinux_type'])} {quote(params['path'])} 2>/dev/null || {_sudo(params)}semanage fcontext -m -t {quote(params['selinux_type'])} {quote(params['path'])}; echo {CHANGE_MARKER}"
        else:
            command = f"{_sudo(params)}semanage fcontext -d {quote(params['path'])} && echo {CHANGE_MARKER} || true"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="selinux.context failed")


class SelinuxRestoreconPlugin(BasePlugin):
    name = "selinux.restorecon"
    description = "Run restorecon on a remote path."
    required_params = ("path",)
    optional_params = ("recursive", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        flags = "-R" if bool(params.get("recursive", False)) else ""
        rc, out, err = exec_remote(context, f"{_sudo(params)}restorecon {flags} {quote(params['path'])} && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="selinux.restorecon failed")


class ApparmorStatusPlugin(BasePlugin):
    name = "apparmor.status"
    description = "Read AppArmor status."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, f"{_sudo(params)}aa-status")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="apparmor.status failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"status": out})


class ApparmorProfilePlugin(BasePlugin):
    name = "apparmor.profile"
    description = "Set an AppArmor profile to enforce or complain mode."
    required_params = ("profile", "state")
    optional_params = ("sudo",)
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if str(params["state"]) not in {"enforce", "complain"}:
            raise PluginValidationError("apparmor.profile state must be enforce or complain")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        tool = "aa-enforce" if str(params["state"]) == "enforce" else "aa-complain"
        rc, out, err = exec_remote(context, f"{_sudo(params)}{tool} {quote(params['profile'])} && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="apparmor.profile failed")


class ApparmorReloadPlugin(BasePlugin):
    name = "apparmor.reload"
    description = "Reload one AppArmor profile file or the AppArmor service."
    optional_params = ("profile", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        if params.get("profile"):
            command = f"{_sudo(params)}apparmor_parser -r {quote(params['profile'])} && echo {CHANGE_MARKER}"
        else:
            command = f"{_sudo(params)}systemctl reload apparmor && echo {CHANGE_MARKER}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="apparmor.reload failed")

class SelinuxPortPlugin(BasePlugin):
    name = "selinux.port"
    description = "Manage a persistent SELinux port type mapping with semanage port."
    required_params = ("port", "protocol", "selinux_type")
    optional_params = ("state", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        desired = f"{params.get('state', 'present')} {params['protocol']}/{params['port']} -> {params['selinux_type']}"
        return [{"path": f"selinux-port:{params['protocol']}/{params['port']}", "kind": "selinux-port-plan", "diff": desired + "\n"}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state == "present":
            return [f"{_sudo(params)}semanage port -a -t {quote(params['selinux_type'])} -p {quote(params['protocol'])} {quote(params['port'])} 2>/dev/null || {_sudo(params)}semanage port -m -t {quote(params['selinux_type'])} -p {quote(params['protocol'])} {quote(params['port'])}"]
        if state == "absent":
            return [f"{_sudo(params)}semanage port -d -p {quote(params['protocol'])} {quote(params['port'])} || true"]
        raise PluginValidationError("selinux.port state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="selinux.port failed")


class SelinuxFcontextPlugin(SelinuxContextPlugin):
    name = "selinux.fcontext"
    description = "Manage a persistent SELinux fcontext mapping with semanage fcontext."
