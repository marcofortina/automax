# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux kernel parameter and module management plugins."""

from __future__ import annotations

import posixpath
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


class SysctlGetPlugin(BasePlugin):
    name = "sysctl.get"
    description = "Read a Linux sysctl value."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"sysctl -n {quote(params['name'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="sysctl.get failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"name": params["name"], "value": out.strip()})


class SysctlSetPlugin(BasePlugin):
    name = "sysctl.set"
    description = "Set a Linux sysctl value at runtime and/or persistently."
    required_params = ("name", "value")
    optional_params = ("runtime", "persist", "file", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        runtime = bool(params.get("runtime", True))
        persist = bool(params.get("persist", False))
        if not runtime and not persist:
            raise PluginValidationError("sysctl.set requires runtime=true and/or persist=true")
        name = str(params["name"])
        value = str(params["value"])
        file_path = str(params.get("file", "/etc/sysctl.d/99-automax.conf"))
        commands = []
        if runtime:
            commands.append(f"{_sudo(params)}sysctl -w {quote(name + '=' + value)}")
        if persist:
            pattern = "^" + name.replace(".", "\\.") + "[[:space:]]*="
            replacement = name + " = " + value
            commands.append(f"{_sudo(params)}mkdir -p {quote(posixpath.dirname(file_path))}")
            commands.append(
                f"if grep -Eq {quote(pattern)} {quote(file_path)} 2>/dev/null; then "
                f"{_sudo(params)}sed -i {quote('s#' + pattern + '.*#' + replacement + '#')} {quote(file_path)}; "
                f"else printf '%s\\n' {quote(replacement)} | {_sudo(params)}tee -a {quote(file_path)} >/dev/null; fi"
            )
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        runtime = bool(params.get("runtime", True))
        persist = bool(params.get("persist", False))
        if not runtime and not persist:
            raise PluginValidationError("sysctl.set requires runtime=true and/or persist=true")
        name = str(params["name"])
        value = str(params["value"])
        file_path = str(params.get("file", "/etc/sysctl.d/99-automax.conf"))
        script = r'''
set -eu
name=$1
value=$2
runtime=$3
persist=$4
file=$5
changed=0
if [ "$runtime" = true ]; then
  current=$(sysctl -n "$name" 2>/dev/null || true)
  if [ "$current" != "$value" ]; then
    sysctl -w "$name=$value" >/dev/null
    changed=1
  fi
fi
if [ "$persist" = true ]; then
  mkdir -p "$(dirname "$file")"
  touch "$file"
  tmp=$(mktemp)
  awk -v key="$name" 'BEGIN{done=0} $1==key && $2=="=" {if(!done){print key " = " ENVIRON["AUTOMAX_SYSCTL_VALUE"]; done=1}; next} {print} END{if(!done) print key " = " ENVIRON["AUTOMAX_SYSCTL_VALUE"]}' "$file" > "$tmp"
  if ! cmp -s "$tmp" "$file"; then
    cat "$tmp" > "$file"
    changed=1
  fi
  rm -f "$tmp"
fi
if [ "$changed" = 1 ]; then echo __AUTOMAX_CHANGED__; fi
'''
        command = (
            f"AUTOMAX_SYSCTL_VALUE={quote(value)} {_sudo(params)}sh -s -- "
            f"{quote(name)} {quote(value)} {quote(str(runtime).lower())} {quote(str(persist).lower())} {quote(file_path)} <<'SH'\n{script}\nSH"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="sysctl.set failed", data={"name": name, "value": value})


class SysctlPersistPlugin(BasePlugin):
    name = "sysctl.persist"
    description = "Persist a Linux sysctl value without applying it immediately."
    required_params = ("name", "value")
    optional_params = ("file", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        rendered = dict(params)
        rendered["runtime"] = False
        rendered["persist"] = True
        return SysctlSetPlugin().manual_commands(rendered, context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        params = dict(params)
        params["runtime"] = False
        params["persist"] = True
        return SysctlSetPlugin().execute(params, context)


class SysctlReloadPlugin(BasePlugin):
    name = "sysctl.reload"
    description = "Reload Linux sysctl settings from a file or all configured files."
    optional_params = ("file", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if params.get("file"):
            return [f"{_sudo(params)}sysctl -p {quote(params['file'])}"]
        return [f"{_sudo(params)}sysctl --system"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        command = self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="sysctl.reload failed")


class KernelModuleLoadPlugin(BasePlugin):
    name = "kernel.module.load"
    description = "Load a Linux kernel module and optionally persist it."
    required_params = ("name",)
    optional_params = ("persist", "file", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        module = str(params["name"])
        commands = [f"{_sudo(params)}modprobe {quote(module)}"]
        if bool(params.get("persist", False)):
            file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
            commands.append(f"grep -Fx -- {quote(module)} {quote(file_path)} >/dev/null 2>&1 || printf '%s\\n' {quote(module)} | {_sudo(params)}tee -a {quote(file_path)} >/dev/null")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        module = str(params["name"])
        persist = bool(params.get("persist", False))
        file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
        script = r'''
set -eu
module=$1
persist=$2
file=$3
changed=0
if ! lsmod | awk '{print $1}' | grep -Fx -- "$module" >/dev/null; then
  modprobe "$module"
  changed=1
fi
if [ "$persist" = true ]; then
  mkdir -p "$(dirname "$file")"
  touch "$file"
  if ! grep -Fx -- "$module" "$file" >/dev/null; then
    printf '%s\n' "$module" >> "$file"
    changed=1
  fi
fi
if [ "$changed" = 1 ]; then echo __AUTOMAX_CHANGED__; fi
'''
        command = f"{_sudo(params)}sh -s -- {quote(module)} {quote(str(persist).lower())} {quote(file_path)} <<'SH'\n{script}\nSH"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="kernel.module.load failed")


class KernelModuleUnloadPlugin(BasePlugin):
    name = "kernel.module.unload"
    description = "Unload a Linux kernel module and optionally remove persisted entries."
    required_params = ("name",)
    optional_params = ("persist", "file", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        module = str(params["name"])
        commands = [f"{_sudo(params)}modprobe -r {quote(module)}"]
        if bool(params.get("persist", False)):
            file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
            commands.append(f"test ! -e {quote(file_path)} || sed -i {quote('/^' + module + '$/d')} {quote(file_path)}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        module = str(params["name"])
        persist = bool(params.get("persist", False))
        file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
        script = r'''
set -eu
module=$1
persist=$2
file=$3
changed=0
if lsmod | awk '{print $1}' | grep -Fx -- "$module" >/dev/null; then
  modprobe -r "$module"
  changed=1
fi
if [ "$persist" = true ] && [ -e "$file" ]; then
  tmp=$(mktemp)
  grep -Fxv -- "$module" "$file" > "$tmp" || true
  if ! cmp -s "$tmp" "$file"; then
    cat "$tmp" > "$file"
    changed=1
  fi
  rm -f "$tmp"
fi
if [ "$changed" = 1 ]; then echo __AUTOMAX_CHANGED__; fi
'''
        command = f"{_sudo(params)}sh -s -- {quote(module)} {quote(str(persist).lower())} {quote(file_path)} <<'SH'\n{script}\nSH"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="kernel.module.unload failed")


class KernelModulePersistPlugin(BasePlugin):
    name = "kernel.module.persist"
    description = "Persist a Linux kernel module for loading at boot."
    required_params = ("name",)
    optional_params = ("state", "file", "sudo")
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        module = str(params["name"])
        file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
        if state == "present":
            return [f"{_sudo(params)}mkdir -p {quote('/etc/modules-load.d')} && grep -Fx -- {quote(module)} {quote(file_path)} >/dev/null 2>&1 || printf '%s\\n' {quote(module)} | {_sudo(params)}tee -a {quote(file_path)} >/dev/null"]
        return [f"test ! -e {quote(file_path)} || sed -i {quote('/^' + module + '$/d')} {quote(file_path)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("kernel.module.persist state must be present or absent")
        module = str(params["name"])
        file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
        if state == "present":
            command = f"{_sudo(params)}mkdir -p {quote('/etc/modules-load.d')} && {_sudo(params)}touch {quote(file_path)} && grep -Fx -- {quote(module)} {quote(file_path)} >/dev/null || {{ echo {quote(module)} | {_sudo(params)}tee -a {quote(file_path)} >/dev/null && echo {CHANGE_MARKER}; }}"
        else:
            command = f"if test -e {quote(file_path)}; then tmp=$(mktemp); grep -Fxv -- {quote(module)} {quote(file_path)} > $tmp || true; if cmp -s $tmp {quote(file_path)}; then rm -f $tmp; else {_sudo(params)}cp $tmp {quote(file_path)} && rm -f $tmp && echo {CHANGE_MARKER}; fi; fi"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="kernel.module.persist failed")
