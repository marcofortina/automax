# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux kernel parameter and module management plugins."""

from __future__ import annotations

import posixpath
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_stdin, quote, result_from_remote, shell_var_ref, sudo_prefix, tempfile_command



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
            commands.append(f"{sudo_prefix(params, default=True)}sysctl -w {quote(name + '=' + value)}")
        if persist:
            pattern = "^" + name.replace(".", "\\.") + "[[:space:]]*="
            replacement = name + " = " + value
            commands.append(f"{sudo_prefix(params, default=True)}mkdir -p {quote(posixpath.dirname(file_path))}")
            commands.append(
                f"if grep -Eq {quote(pattern)} {quote(file_path)} 2>/dev/null; then "
                f"{sudo_prefix(params, default=True)}sed -i {quote('s#' + pattern + '.*#' + replacement + '#')} {quote(file_path)}; "
                f"else printf '%s\\n' {quote(replacement)} | {sudo_prefix(params, default=True)}tee -a {quote(file_path)} >/dev/null; fi"
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
        command = heredoc_to_stdin(
            f"AUTOMAX_SYSCTL_VALUE={quote(value)} {sudo_prefix(params, default=True)}sh -s -- "
            f"{quote(name)} {quote(value)} {quote(str(runtime).lower())} {quote(str(persist).lower())} {quote(file_path)}",
            script,
            prefix="AUTOMAX_SH",
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
            return [f"{sudo_prefix(params, default=True)}sysctl -p {quote(params['file'])}"]
        return [f"{sudo_prefix(params, default=True)}sysctl --system"]

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
        commands = [f"{sudo_prefix(params, default=True)}modprobe {quote(module)}"]
        if bool(params.get("persist", False)):
            file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
            commands.append(f"grep -Fx -- {quote(module)} {quote(file_path)} >/dev/null 2>&1 || printf '%s\\n' {quote(module)} | {sudo_prefix(params, default=True)}tee -a {quote(file_path)} >/dev/null")
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
        command = heredoc_to_stdin(
            f"{sudo_prefix(params, default=True)}sh -s -- {quote(module)} {quote(str(persist).lower())} {quote(file_path)}",
            script,
            prefix="AUTOMAX_SH",
        )
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
        commands = [f"{sudo_prefix(params, default=True)}modprobe -r {quote(module)}"]
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
        command = heredoc_to_stdin(
            f"{sudo_prefix(params, default=True)}sh -s -- {quote(module)} {quote(str(persist).lower())} {quote(file_path)}",
            script,
            prefix="AUTOMAX_SH",
        )
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
            return [f"{sudo_prefix(params, default=True)}mkdir -p {quote('/etc/modules-load.d')} && grep -Fx -- {quote(module)} {quote(file_path)} >/dev/null 2>&1 || printf '%s\\n' {quote(module)} | {sudo_prefix(params, default=True)}tee -a {quote(file_path)} >/dev/null"]
        return [f"test ! -e {quote(file_path)} || sed -i {quote('/^' + module + '$/d')} {quote(file_path)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("kernel.module.persist state must be present or absent")
        module = str(params["name"])
        file_path = str(params.get("file", f"/etc/modules-load.d/{module}.conf"))
        if state == "present":
            command = f"{sudo_prefix(params, default=True)}mkdir -p {quote('/etc/modules-load.d')} && {sudo_prefix(params, default=True)}touch {quote(file_path)} && grep -Fx -- {quote(module)} {quote(file_path)} >/dev/null || {{ echo {quote(module)} | {sudo_prefix(params, default=True)}tee -a {quote(file_path)} >/dev/null && echo {CHANGE_MARKER}; }}"
        else:
            command = f"if test -e {quote(file_path)}; then tmp=$(mktemp); grep -Fxv -- {quote(module)} {quote(file_path)} > $tmp || true; if cmp -s $tmp {quote(file_path)}; then rm -f $tmp; else {sudo_prefix(params, default=True)}cp $tmp {quote(file_path)} && rm -f $tmp && echo {CHANGE_MARKER}; fi; fi"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="kernel.module.persist failed")

class KernelBootParamPlugin(BasePlugin):
    name = "kernel.boot_param"
    description = "Ensure a persistent kernel boot parameter in GRUB-compatible defaults with backup and grub config regeneration."
    required_params = ("name",)
    optional_params = ("value", "state", "path", "backup", "backup_suffix", "update_grub", "sudo")
    opens_remote_session = True

    def _token(self, params: Dict[str, Any]) -> str:
        if params.get("value") is None or str(params.get("value")) == "":
            return str(params["name"])
        return f"{params['name']}={params['value']}"

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", "/etc/default/grub"))

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        token = self._token(params)
        state = str(params.get("state", "present"))
        return [{"path": self._path(params), "kind": "kernel-boot-plan", "diff": f"{state} GRUB_CMDLINE_LINUX token: {token}\n"}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("kernel.boot_param state must be present or absent")
        path = self._path(params)
        token = self._token(params)
        sudo = sudo_prefix(params, default=True)
        script = r'''
set -eu
path=$1
state=$2
token=$3
tmp=$(mktemp)
if [ ! -e "$path" ]; then echo 'missing grub defaults file' >&2; exit 1; fi
awk -v state="$state" -v token="$token" '
  BEGIN{done=0}
  /^GRUB_CMDLINE_LINUX=/ {
    line=$0
    sub(/^GRUB_CMDLINE_LINUX="/, "", line)
    sub(/"$/, "", line)
    n=split(line, parts, " ")
    out=""
    found=0
    split(token, kv, "=")
    for (i=1; i<=n; i++) {
      if (parts[i] == "") continue
      split(parts[i], pkv, "=")
      if (pkv[1] == kv[1]) { found=1; if (state == "present") parts[i]=token; else parts[i]="" }
      if (parts[i] != "") out=(out == "" ? parts[i] : out " " parts[i])
    }
    if (state == "present" && !found) out=(out == "" ? token : out " " token)
    print "GRUB_CMDLINE_LINUX=\"" out "\""
    done=1
    next
  }
  {print}
  END{if(!done && state == "present") print "GRUB_CMDLINE_LINUX=\"" token "\""}
' "$path" > "$tmp"
cat "$tmp"
rm -f "$tmp"
'''
        commands = []
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        tmp_var = "automax_grub_tmp"
        tmp = shell_var_ref(tmp_var)
        commands.append(tempfile_command(tmp_var, "grub"))
        commands.append(
            heredoc_to_stdin(
                f"{sudo}sh -s -- {quote(path)} {quote(state)} {quote(token)} > {tmp}",
                script,
                prefix="AUTOMAX_SH",
            )
        )
        commands.append(f"{sudo}install -m 0644 {tmp} {quote(path)} && rm -f {tmp}")
        if bool(params.get("update_grub", True)):
            commands.append(f"if command -v update-grub >/dev/null 2>&1; then {sudo}update-grub; elif command -v grub2-mkconfig >/dev/null 2>&1; then {sudo}grub2-mkconfig -o /boot/grub2/grub.cfg; fi")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="kernel.boot_param failed")
