# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Additional operation, assertion and hardening plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError, ReadOnlyCommandPlugin, RenderedFileInstallMixin
from automax.plugins.remote_utils import cleanup_trap_command, CHANGE_MARKER, SUDO_NON_INTERACTIVE, exec_remote, heredoc_to_file_expr, shell_var_ref, tempfile_command, quote, result_from_remote, sudo_prefix



def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


def _state(params: Dict[str, Any], allowed: set[str] = {"present", "absent"}) -> str:
    state = str(params.get("state", "present"))
    if state not in allowed:
        raise PluginValidationError(f"state must be one of: {', '.join(sorted(allowed))}")
    return state


# AppArmor
class ApparmorEnforcePlugin(BasePlugin):
    name = "security.apparmor.enforce"
    description = "Put one AppArmor profile in enforcing mode."
    required_params = ("profile",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}aa-enforce {quote(params['profile'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.apparmor.enforce failed")


class ApparmorComplainPlugin(ApparmorEnforcePlugin):
    name = "security.apparmor.complain"
    description = "Put one AppArmor profile in complain mode."

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}aa-complain {quote(params['profile'])}"]


class ApparmorDisablePlugin(ApparmorEnforcePlugin):
    name = "security.apparmor.disable"
    description = "Disable one AppArmor profile after explicit confirmation."
    optional_params = ("confirm", "sudo")

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not bool(params.get("confirm", False)):
            raise PluginValidationError("security.apparmor.disable requires confirm=true")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}aa-disable {quote(params['profile'])}"]


class ApparmorProfileAssertPlugin(ReadOnlyCommandPlugin):
    name = "security.apparmor.profile_check"
    description = "Assert that an AppArmor profile is loaded in the expected mode."
    required_params = ("profile", "state")
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        state = str(params["state"])
        if state not in {"enforce", "complain", "disabled"}:
            raise PluginValidationError("security.apparmor.profile_check state must be enforce, complain or disabled")
        profile = quote(params["profile"])
        if state == "disabled":
            return [f"! {sudo_prefix(params, default=True)}aa-status 2>/dev/null | grep -F -- {profile}"]
        return [f"{sudo_prefix(params, default=True)}aa-status 2>/dev/null | grep -F -- {profile} | grep -Fi -- {quote(state)}"]


class ApparmorParserValidatePlugin(ReadOnlyCommandPlugin):
    name = "security.apparmor.validate"
    description = "Validate an AppArmor profile with apparmor_parser before applying it."
    required_params = ("profile",)
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}apparmor_parser -Q {quote(params['profile'])}"]


# auditd
class AuditdRulesFactsPlugin(ReadOnlyCommandPlugin):
    name = "security.audit.rules.facts"
    description = "List active auditd rules and persistent rules.d files."
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=True)}auditctl -l; printf '\\n### persistent rules\\n'; for f in /etc/audit/rules.d/*.rules; do test -f \"$f\" || continue; echo \"$f\"; sed -n '1,200p' \"$f\"; done"]


class AuditdWatchPlugin(BasePlugin):
    name = "security.audit.watch"
    description = "Install an auditd filesystem watch rule."
    required_params = ("name", "path", "permissions", "key")
    optional_params = ("backup", "backup_suffix", "reload", "sudo")
    opens_remote_session = True

    def _rule(self, params: Dict[str, Any]) -> str:
        return f"-w {params['path']} -p {params['permissions']} -k {params['key']}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _diff(f"/etc/audit/rules.d/{params['name']}.rules", self._rule(params) + "\n", "auditd-watch-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = f"/etc/audit/rules.d/{params['name']}.rules"
        rule = self._rule(params)
        commands = []
        if bool(params.get("backup", True)):
            commands.append(f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        commands.append(f"printf '%s\\n' {quote(rule)} | {sudo_prefix(params, default=True)}tee {quote(path)} >/dev/null")
        if bool(params.get("reload", True)):
            commands.append(f"if command -v augenrules >/dev/null 2>&1; then {sudo_prefix(params, default=True)}augenrules --load; else {sudo_prefix(params, default=True)}auditctl -R {quote(path)}; fi")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.audit.watch failed")


class AuditdSyscallPlugin(AuditdWatchPlugin):
    name = "security.audit.syscall"
    description = "Install an auditd syscall rule."
    required_params = ("name", "syscalls", "key")
    optional_params = ("arch", "action", "filters", "backup", "backup_suffix", "reload", "sudo")

    def _rule(self, params: Dict[str, Any]) -> str:
        syscalls = " ".join(f"-S {item}" for item in _as_list(params["syscalls"]))
        filters = " ".join(f"-F {item}" for item in _as_list(params.get("filters")))
        return f"-a {params.get('action', 'always,exit')} -F arch={params.get('arch', 'b64')} {syscalls} {filters} -k {params['key']}".strip()


class AuditdSearchPlugin(ReadOnlyCommandPlugin):
    name = "security.audit.search"
    description = "Search audit events by key, user or time window."
    optional_params = ("key", "user", "start", "end", "sudo")
    parameter_schema = {
        "key": {"type": "string", "default": None, "description": "Audit event key."},
        "user": {"type": "string", "default": None, "description": "Audit user name or numeric UID."},
        "start": {"type": "string", "default": None, "description": "Audit search start time."},
        "end": {"type": "string", "default": None, "description": "Audit search end time."},
    }

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        args = []
        if params.get("key"):
            args.append(f"-k {quote(params['key'])}")
        if params.get("user"):
            args.append(f"-ua {quote(params['user'])}")
        if params.get("start"):
            args.append(f"-ts {quote(params['start'])}")
        if params.get("end"):
            args.append(f"-te {quote(params['end'])}")
        return [f"{sudo_prefix(params, default=True)}ausearch {' '.join(args)}"]


class AuditdBacklogAssertPlugin(ReadOnlyCommandPlugin):
    name = "security.audit.backlog_check"
    description = "Assert auditd lost-event count and backlog are below thresholds."
    optional_params = ("max_lost", "max_backlog", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        max_lost = int(params.get("max_lost", 0))
        max_backlog = int(params.get("max_backlog", 8192))
        return [f"{sudo_prefix(params, default=True)}auditctl -s | awk -v max_lost={max_lost} -v max_backlog={max_backlog} '$1==\"lost\" && $2>max_lost {{ bad=1 }} $1==\"backlog\" && $2>max_backlog {{ bad=1 }} {{print}} END {{ exit bad }}'"]


# udev
class UdevValidatePlugin(ReadOnlyCommandPlugin):
    name = "udev.validate"
    description = "Validate udev rules file syntax with udevadm test where possible."
    required_params = ("file",)
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"test -r {quote(params['file'])} && grep -nE '^[^#].*(==|=|:=|\\+=)' {quote(params['file'])} >/dev/null"]


class UdevTestPlugin(ReadOnlyCommandPlugin):
    name = "udev.test"
    description = "Run udevadm test for a device sysfs path."
    required_params = ("device",)
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}udevadm test {quote(params['device'])}"]


class UdevFactsPlugin(ReadOnlyCommandPlugin):
    name = "udev.facts"
    description = "Read udev properties for a device path."
    required_params = ("device",)
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}udevadm info --query=property --name {quote(params['device'])}"]


# kernel/sysctl/time
class KernelModuleStatusPlugin(ReadOnlyCommandPlugin):
    name = "kernel.module.status"
    description = "Assert or report kernel module load status."
    required_params = ("module",)
    optional_params = ("state", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        state = str(params.get("state", "loaded"))
        module = quote(params["module"])
        if state == "absent":
            return [f"! lsmod | awk '{{print $1}}' | grep -Fx -- {module}"]
        return [f"lsmod | awk '{{print $1}}' | grep -Fx -- {module}"]


class KernelModuleBlacklistPlugin(BasePlugin):
    name = "kernel.module.blacklist"
    description = "Install or remove a persistent kernel module blacklist drop-in."
    required_params = ("module",)
    optional_params = ("state", "file", "backup", "backup_suffix", "sudo")
    opens_remote_session = True
    rendered_file_temp_prefix = "sysctl"
    rendered_file_diff_kind = "sysctl-dropin-plan"

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("file") or f"/etc/modprobe.d/automax-{params['module']}.conf")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        content = "" if _state(params) == "absent" else f"blacklist {params['module']}\ninstall {params['module']} /bin/false\n"
        return _diff(self._path(params), content, "kernel-module-blacklist-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = self._path(params)
        if _state(params) == "absent":
            return [f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}rm -f {quote(path)}"]
        content = f"blacklist {params['module']}\ninstall {params['module']} /bin/false\n"
        tmp_var = "automax_modprobe_tmp"
        tmp = shell_var_ref(tmp_var)
        cmds = [tempfile_command(tmp_var, "modprobe"), cleanup_trap_command(tmp_var), heredoc_to_file_expr(tmp, content)]
        if bool(params.get("backup", True)):
            cmds.append(f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        cmds.append(f"{sudo_prefix(params, default=True)}install -D -m 0644 {tmp} {quote(path)}")
        cmds.append(f"rm -f {tmp}")
        return cmds

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="kernel.module.blacklist failed")


class KernelCmdlineAssertPlugin(ReadOnlyCommandPlugin):
    name = "kernel.cmdline_assert"
    description = "Assert that the running kernel command line contains or omits a parameter."
    required_params = ("param",)
    optional_params = ("state", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        state = _state(params)
        test = f"tr ' ' '\\n' < /proc/cmdline | grep -Fx -- {quote(params['param'])}"
        return [test if state == "present" else f"! {test}"]


class KernelBootParamAbsentPlugin(BasePlugin):
    name = "kernel.boot_param_absent"
    description = "Remove a kernel boot parameter from GRUB defaults after explicit confirmation."
    required_params = ("param",)
    optional_params = ("file", "backup", "backup_suffix", "confirm", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not bool(params.get("confirm", False)):
            raise PluginValidationError("kernel.boot_param_absent requires confirm=true")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = str(params.get("file", "/etc/default/grub"))
        cmds=[]
        if bool(params.get("backup", True)):
            cmds.append(f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}")
        cmds.append(f"{sudo_prefix(params, default=True)}sed -i -E 's/(GRUB_CMDLINE_LINUX[^=]*=\"[^\"]*)\\b{params['param']}\\b ?/\\1/' {quote(path)}")
        sudo = sudo_prefix(params, default=True)
        cmds.append(f"if command -v update-grub >/dev/null 2>&1; then {sudo}update-grub; elif command -v grub2-mkconfig >/dev/null 2>&1; then {sudo}grub2-mkconfig -o /boot/grub2/grub.cfg; fi")
        return cmds

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc,out,err=exec_remote(context," && ".join(self.manual_commands(params,context))+f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="kernel.boot_param_absent failed")


class SysctlAssertPlugin(ReadOnlyCommandPlugin):
    name = "sysctl.assert"
    description = "Assert a runtime sysctl value."
    required_params = ("name", "value")
    optional_params = ("sudo",)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"test \"$({sudo_prefix(params, default=True)}sysctl -n {quote(params['name'])})\" = {quote(params['value'])}"]


class SysctlFactsPlugin(ReadOnlyCommandPlugin):
    name = "sysctl.facts"
    description = "Read one or more sysctl values."
    optional_params = ("names", "sudo")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        names = _as_list(params.get("names"))
        return [f"{sudo_prefix(params, default=True)}sysctl -a" if not names else f"{sudo_prefix(params, default=True)}sysctl {' '.join(quote(item) for item in names)}"]


class SysctlDropinPlugin(RenderedFileInstallMixin, BasePlugin):
    name = "sysctl.dropin"
    description = "Install a sysctl.d drop-in and reload sysctl values."
    required_params = ("name", "settings")
    optional_params = ("file", "reload", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("file") or f"/etc/sysctl.d/{params['name']}.conf")

    def _content(self, params: Dict[str, Any]) -> str:
        settings=params["settings"]
        if not isinstance(settings, dict) or not settings:
            raise PluginValidationError("sysctl.dropin settings must be a non-empty mapping")
        return "".join(f"{k} = {v}\n" for k,v in sorted(settings.items()))

    def rendered_file_path(self, params: Dict[str, Any]) -> str:
        return self._path(params)

    def rendered_file_content(self, params: Dict[str, Any]) -> str:
        return self._content(params)

    def rendered_file_post_install_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if bool(params.get("reload", True)):
            return [f"{self.rendered_file_sudo(params)}sysctl --system"]
        return []


class TimedatectlStatusPlugin(ReadOnlyCommandPlugin):
    name = "timedatectl.status"
    description = "Read timedatectl time, timezone and NTP state."
    optional_params = ("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]: return [f"{sudo_prefix(params, default=True)}timedatectl status"]

class TimedatectlTimezonePlugin(BasePlugin):
    name="timedatectl.timezone"; description="Set system timezone with timedatectl."; required_params=("timezone",); optional_params=("sudo",); opens_remote_session=True
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]: return [f"test \"$({sudo_prefix(params, default=True)}timedatectl show -p Timezone --value)\" = {quote(params['timezone'])} || {sudo_prefix(params, default=True)}timedatectl set-timezone {quote(params['timezone'])}"]
    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc,out,err=exec_remote(context,self.manual_commands(params,context)[0]+f" && echo {CHANGE_MARKER}"); return result_from_remote(rc=rc, stdout=out, stderr=err, message="timedatectl.timezone failed")

class TimedatectlNtpPlugin(TimedatectlTimezonePlugin):
    name="timedatectl.ntp"; description="Enable or disable NTP through timedatectl."; required_params=("enabled",); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        want="yes" if bool(params["enabled"]) else "no"; value="true" if bool(params["enabled"]) else "false"
        return [f"test \"$({sudo_prefix(params, default=True)}timedatectl show -p NTP --value)\" = {quote(want)} || {sudo_prefix(params, default=True)}timedatectl set-ntp {value}"]

class ChronyTrackingAssertPlugin(ReadOnlyCommandPlugin):
    name="chrony.tracking_assert"; description="Assert chrony tracking health using chronyc tracking."; optional_params=("max_offset","max_stratum","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        max_offset=float(params.get("max_offset",1.0)); max_stratum=int(params.get("max_stratum",16))
        return [f"chronyc tracking | awk -F: -v max_offset={max_offset} -v max_stratum={max_stratum} '/Stratum/ {{gsub(/ /,\"\",$2); if ($2>max_stratum) bad=1}} /System time/ {{gsub(/ /,\"\",$2); split($2,a,\"seconds\"); if (a[1]+0>max_offset || a[1]+0<-max_offset) bad=1}} {{print}} END {{exit bad}}'"]


# User/group/sudo facts and assertions
class UserFactsPlugin(ReadOnlyCommandPlugin):
    name="identity.user.facts"; description="Read passwd, shadow lock and group facts for a user."; required_params=("user",); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]: return [f"getent passwd {quote(params['user'])}; id {quote(params['user'])}; {sudo_prefix(params, default=True)}passwd -S {quote(params['user'])} 2>/dev/null || true"]

class UserShellAssertPlugin(ReadOnlyCommandPlugin):
    name="identity.user.shell_check"; description="Assert a user's login shell."; required_params=("user","shell"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"test \"$(getent passwd {quote(params['user'])} | cut -d: -f7)\" = {quote(params['shell'])}"]

class UserHomeAssertPlugin(ReadOnlyCommandPlugin):
    name="identity.user.home_check"; description="Assert a user's home directory path, owner or mode."; required_params=("user",); optional_params=("path","mode","owner","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        path=f"$(getent passwd {quote(params['user'])} | cut -d: -f6)"; cmds=[]
        if params.get("path"): cmds.append(f"test \"{path}\" = {quote(params['path'])}")
        if params.get("mode"): cmds.append(f"test \"$(stat -c %a {path})\" = {quote(params['mode'])}")
        if params.get("owner"): cmds.append(f"test \"$(stat -c %U {path})\" = {quote(params['owner'])}")
        return cmds or [f"test -d {path}"]

class UserGroupsAssertPlugin(ReadOnlyCommandPlugin):
    name="identity.user.groups_check"; description="Assert required group membership for a user."; required_params=("user","groups"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        user=quote(params['user']); return [" && ".join(f"id -nG {user} | tr ' ' '\\n' | grep -Fx -- {quote(g)}" for g in _as_list(params['groups']))]

class GroupMembersPlugin(ReadOnlyCommandPlugin):
    name="identity.group.members"; description="List members of a group."; required_params=("group",); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"getent group {quote(params['group'])}"]

class GroupMemberAbsentPlugin(BasePlugin):
    name="identity.group.member.remove"; description="Remove a user from a group after explicit confirmation."; required_params=("user","group"); optional_params=("confirm","sudo"); opens_remote_session=True
    def validate(self, params: Dict[str, Any])->None:
        super().validate(params)
        if not bool(params.get("confirm", False)): raise PluginValidationError("identity.group.member.remove requires confirm=true")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        self.validate(params); return [f"{sudo_prefix(params, default=True)}gpasswd -d {quote(params['user'])} {quote(params['group'])}"]
    def execute(self, params: Dict[str, Any], context: ExecutionContext)->PluginResult:
        rc,out,err=exec_remote(context,self.manual_commands(params,context)[0]+f" && echo {CHANGE_MARKER}"); return result_from_remote(rc=rc, stdout=out, stderr=err, message="identity.group.member.remove failed")

class SudoListPlugin(ReadOnlyCommandPlugin):
    name="security.sudo.list"; description="List sudo privileges for a user."; required_params=("user",); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"{sudo_prefix(params, default=True)}sudo -l -U {quote(params['user'])}"]

class SudoAssertPlugin(ReadOnlyCommandPlugin):
    name="security.sudo.check"; description="Assert sudo -l output contains a rule fragment."; required_params=("user","rule"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"{sudo_prefix(params, default=True)}sudo -l -U {quote(params['user'])} | grep -F -- {quote(params['rule'])}"]

class SudoCanRunPlugin(ReadOnlyCommandPlugin):
    name="security.sudo.can_run"; description="Assert that a user can run a command via sudo without prompting."; required_params=("user","command"); optional_params=("run_as","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        run_as=f" -u {quote(params.get('run_as'))}" if params.get("run_as") else ""; return [f"{sudo_prefix(params, default=True)}{SUDO_NON_INTERACTIVE} -l -U {quote(params['user'])}{run_as} {quote(params['command'])}"]


# Mount/fstab/block safety
class MountAssertPlugin(ReadOnlyCommandPlugin):
    name="mount.assert"; description="Assert a mountpoint is mounted, optionally from source and fstype."; required_params=("path",); optional_params=("source","fstype","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        cmd=f"findmnt -n {quote(params['path'])}"; filters=[]
        if params.get("source"): filters.append(f"grep -F -- {quote(params['source'])}")
        if params.get("fstype"): filters.append(f"grep -F -- {quote(params['fstype'])}")
        return [" | ".join([cmd,*filters])]

class MountOptionsAssertPlugin(ReadOnlyCommandPlugin):
    name="mount.options_assert"; description="Assert required mount options are active."; required_params=("path","options"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        cmd=f"findmnt -n -o OPTIONS {quote(params['path'])}"; return [" && ".join(f"{cmd} | tr ',' '\\n' | grep -Fx -- {quote(o)}" for o in _as_list(params['options']))]

class FstabAbsentPlugin(BasePlugin):
    name="fstab.absent"; description="Remove fstab entries matching a mountpoint or source after confirmation."; required_params=(); optional_params=("path","source","file","confirm","backup","backup_suffix","sudo"); opens_remote_session=True
    def validate(self, params: Dict[str, Any])->None:
        if not (params.get("path") or params.get("source")): raise PluginValidationError("fstab.absent requires path or source")
        if not bool(params.get("confirm", False)): raise PluginValidationError("fstab.absent requires confirm=true")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        self.validate(params); file=str(params.get("file","/etc/fstab")); pattern=params.get("path") or params.get("source"); cmds=[]
        if bool(params.get("backup", True)): cmds.append(f"{sudo_prefix(params, default=True)}cp -p {quote(file)} {quote(file + str(params.get('backup_suffix','.bak')))}")
        cmds.append(f"{sudo_prefix(params, default=True)}awk '$0 ~ /^#/ || $0 !~ {quote(pattern)}' {quote(file)} | {sudo_prefix(params, default=True)}tee {quote(file)} >/dev/null")
        return cmds
    def execute(self, params: Dict[str, Any], context: ExecutionContext)->PluginResult:
        rc,out,err=exec_remote(context," && ".join(self.manual_commands(params,context))+f" && echo {CHANGE_MARKER}"); return result_from_remote(rc=rc, stdout=out, stderr=err, message="fstab.absent failed")

class FstabAssertPlugin(ReadOnlyCommandPlugin):
    name="fstab.assert"; description="Assert an fstab entry exists for source, path or fstype."; optional_params=("path","source","fstype","file","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        file=quote(params.get("file","/etc/fstab")); cmds=[f"grep -Ev '^[[:space:]]*(#|$)' {file}"]
        for key in ("source","path","fstype"):
            if params.get(key): cmds.append(f"grep -F -- {quote(params[key])}")
        return [" | ".join(cmds)]

class BlockSizeAssertPlugin(ReadOnlyCommandPlugin):
    name="block.size_assert"; description="Assert block device size in bytes."; required_params=("device","size"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"test \"$({sudo_prefix(params, default=True)}blockdev --getsize64 {quote(params['device'])})\" = {quote(params['size'])}"]

class BlockFsAssertPlugin(ReadOnlyCommandPlugin):
    name="block.fs_assert"; description="Assert block device filesystem type."; required_params=("device","fstype"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"test \"$({sudo_prefix(params, default=True)}blkid -o value -s TYPE {quote(params['device'])})\" = {quote(params['fstype'])}"]

class BlockMountpointAssertPlugin(ReadOnlyCommandPlugin):
    name="block.mountpoint_assert"; description="Assert a block device is mounted at a path."; required_params=("device","path"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"findmnt -n -S {quote(params['device'])} -T {quote(params['path'])}"]

class BlockEmptyAssertPlugin(ReadOnlyCommandPlugin):
    name="block.empty_assert"; description="Assert a block device has no detectable signature before destructive use."; required_params=("device",); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"! {sudo_prefix(params, default=True)}blkid {quote(params['device'])}"]

class BlockNotMountedAssertPlugin(ReadOnlyCommandPlugin):
    name="block.not_mounted_assert"; description="Assert a block device is not mounted."; required_params=("device",); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"! findmnt -n -S {quote(params['device'])}"]


# PAM stack helpers
class PamIncludeAssertPlugin(ReadOnlyCommandPlugin):
    name="security.pam.include_check"; description="Assert a PAM service includes another stack."; required_params=("service","include"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"grep -Eq '(^|[[:space:]])(include|substack|@include)[[:space:]]+{params['include']}($|[[:space:]])' /etc/pam.d/{quote(params['service'])}"]

class PamModuleAssertPlugin(ReadOnlyCommandPlugin):
    name="security.pam.module_check"; description="Assert a PAM module line exists in a service."; required_params=("service","module"); optional_params=("type","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        prefix=f"^{params.get('type')}[[:space:]]+" if params.get("type") else ""; return [f"grep -Eq {quote(prefix + '.*' + str(params['module']))} /etc/pam.d/{quote(params['service'])}"]

class PamOrderAssertPlugin(ReadOnlyCommandPlugin):
    name="security.pam.order_check"; description="Assert one PAM line appears before another."; required_params=("service","before","after"); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"awk '/{params['before']}/{{b=NR}} /{params['after']}/{{a=NR}} END{{exit !(b && a && b<a)}}' /etc/pam.d/{quote(params['service'])}"]

class PamBackupPlugin(BasePlugin):
    name="security.pam.backup"; description="Backup one PAM service file."; required_params=("service",); optional_params=("dest","sudo"); opens_remote_session=True
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        src=f"/etc/pam.d/{params['service']}"; dest=str(params.get("dest", src+".bak")); return [f"{sudo_prefix(params, default=True)}cp -p {quote(src)} {quote(dest)}"]
    def execute(self, params: Dict[str, Any], context: ExecutionContext)->PluginResult:
        rc,out,err=exec_remote(context,self.manual_commands(params,context)[0]+f" && echo {CHANGE_MARKER}"); return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.pam.backup failed")

class PamRestorePlugin(PamBackupPlugin):
    name="security.pam.restore"; description="Restore one PAM service file from backup after confirmation."; required_params=("service","src"); optional_params=("confirm","sudo")
    def validate(self, params: Dict[str, Any])->None:
        super().validate(params)
        if not bool(params.get("confirm", False)): raise PluginValidationError("security.pam.restore requires confirm=true")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        self.validate(params); dest=f"/etc/pam.d/{params['service']}"; return [f"{sudo_prefix(params, default=True)}cp -p {quote(params['src'])} {quote(dest)}"]


# Firewall backend-specific extras
class FirewalldSourcePlugin(BasePlugin):
    name="network.firewall.firewalld.source"; description="Manage a firewalld source in a zone."; required_params=("source",); optional_params=("zone","state","permanent","reload","sudo"); parameter_schema={"source": {"type": "string", "description": "firewalld source address, network or ipset."}}; opens_remote_session=True
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        state=_state(params); zone=f"--zone={quote(params['zone'])} " if params.get("zone") else ""; permanent="--permanent " if bool(params.get("permanent", True)) else ""; action="add-source" if state=="present" else "remove-source"; query_cmd=f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-source={quote(params['source'])}"; expected="0" if state=="present" else "1"; cmd=f"if {query_cmd} >/dev/null 2>&1; then present=0; else present=1; fi; if [ \"$present\" = {expected} ]; then true; else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(params['source'])} && echo {CHANGE_MARKER}; fi"; return [cmd + (f"; {sudo_prefix(params, default=True)}firewall-cmd --reload" if bool(params.get("reload", False)) else "")]
    def execute(self, params: Dict[str, Any], context: ExecutionContext)->PluginResult:
        rc,out,err=exec_remote(context,self.manual_commands(params,context)[0]); return result_from_remote(rc=rc, stdout=out, stderr=err, message="network.firewall.firewalld.source failed")

class FirewalldIcmpBlockPlugin(FirewalldSourcePlugin):
    name="network.firewall.firewalld.icmp_block"; description="Manage a firewalld ICMP block."; required_params=("icmp_type",); optional_params=("zone","state","permanent","reload","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        state=_state(params); zone=f"--zone={quote(params['zone'])} " if params.get("zone") else ""; permanent="--permanent " if bool(params.get("permanent", True)) else ""; action="add-icmp-block" if state=="present" else "remove-icmp-block"; query_cmd=f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-icmp-block={quote(params['icmp_type'])}"; expected="0" if state=="present" else "1"; cmd=f"if {query_cmd} >/dev/null 2>&1; then present=0; else present=1; fi; if [ \"$present\" = {expected} ]; then true; else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(params['icmp_type'])} && echo {CHANGE_MARKER}; fi"; return [cmd + (f"; {sudo_prefix(params, default=True)}firewall-cmd --reload" if bool(params.get("reload", False)) else "")]

class FirewalldMasqueradePlugin(FirewalldSourcePlugin):
    name="network.firewall.firewalld.masquerade"; description="Manage firewalld masquerading for a zone."; required_params=(); optional_params=("zone","state","permanent","reload","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        state=_state(params); zone=f"--zone={quote(params['zone'])} " if params.get("zone") else ""; permanent="--permanent " if bool(params.get("permanent", True)) else ""; action="add-masquerade" if state=="present" else "remove-masquerade"; query_cmd=f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-masquerade"; expected="0" if state=="present" else "1"; cmd=f"if {query_cmd} >/dev/null 2>&1; then present=0; else present=1; fi; if [ \"$present\" = {expected} ]; then true; else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action} && echo {CHANGE_MARKER}; fi"; return [cmd + (f"; {sudo_prefix(params, default=True)}firewall-cmd --reload" if bool(params.get("reload", False)) else "")]

class FirewalldForwardPortPlugin(FirewalldSourcePlugin):
    name="network.firewall.firewalld.forward_port"; description="Manage firewalld forward-port rules."; required_params=("port","to_port"); optional_params=("protocol","to_addr","zone","state","permanent","reload","sudo")
    def _spec(self, params: Dict[str, Any])->str:
        spec=f"port={params['port']}:proto={params.get('protocol','tcp')}:toport={params['to_port']}"; return spec + (f":toaddr={params['to_addr']}" if params.get("to_addr") else "")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        state=_state(params); zone=f"--zone={quote(params['zone'])} " if params.get("zone") else ""; permanent="--permanent " if bool(params.get("permanent", True)) else ""; action="add-forward-port" if state=="present" else "remove-forward-port"; spec=self._spec(params); query_cmd=f"{sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--query-forward-port={quote(spec)}"; expected="0" if state=="present" else "1"; cmd=f"if {query_cmd} >/dev/null 2>&1; then present=0; else present=1; fi; if [ \"$present\" = {expected} ]; then true; else {sudo_prefix(params, default=True)}firewall-cmd {zone}{permanent}--{action}={quote(spec)} && echo {CHANGE_MARKER}; fi"; return [cmd + (f"; {sudo_prefix(params, default=True)}firewall-cmd --reload" if bool(params.get("reload", False)) else "")]

class NftablesRulesetAssertPlugin(ReadOnlyCommandPlugin):
    name="network.firewall.nftables.ruleset_assert"; description="Assert the active nftables ruleset contains a fragment."; required_params=("fragment",); optional_params=("sudo",)
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: return [f"{sudo_prefix(params, default=True)}nft list ruleset | grep -F -- {quote(params['fragment'])}"]

class NftablesRollbackFilePlugin(BasePlugin):
    name="network.firewall.nftables.rollback_file"; description="Apply an nftables rollback ruleset file after explicit confirmation."; required_params=("file",); optional_params=("confirm","sudo"); opens_remote_session=True
    def validate(self, params: Dict[str, Any])->None:
        super().validate(params)
        if not bool(params.get("confirm", False)): raise PluginValidationError("network.firewall.nftables.rollback_file requires confirm=true")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: self.validate(params); return [f"{sudo_prefix(params, default=True)}nft -c -f {quote(params['file'])} && {sudo_prefix(params, default=True)}nft -f {quote(params['file'])}"]
    def execute(self, params: Dict[str, Any], context: ExecutionContext)->PluginResult:
        rc,out,err=exec_remote(context,self.manual_commands(params,context)[0]+f" && echo {CHANGE_MARKER}"); return result_from_remote(rc=rc, stdout=out, stderr=err, message="network.firewall.nftables.rollback_file failed")

class IptablesDeletePlugin(BasePlugin):
    name="network.firewall.iptables.delete"; description="Delete an iptables rule after explicit confirmation."; required_params=("chain","rule"); optional_params=("table","ipv6","confirm","sudo"); opens_remote_session=True
    def validate(self, params: Dict[str, Any])->None:
        super().validate(params)
        if not bool(params.get("confirm", False)): raise PluginValidationError("network.firewall.iptables.delete requires confirm=true")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        self.validate(params); binary="ip6tables" if bool(params.get("ipv6",False)) else "iptables"; table=str(params.get("table","filter")); return [f"{sudo_prefix(params, default=True)}{binary} -t {quote(table)} -C {quote(params['chain'])} {params['rule']} >/dev/null 2>&1 && {sudo_prefix(params, default=True)}{binary} -t {quote(table)} -D {quote(params['chain'])} {params['rule']} || true"]
    def execute(self, params: Dict[str, Any], context: ExecutionContext)->PluginResult:
        rc,out,err=exec_remote(context,self.manual_commands(params,context)[0]+f" && echo {CHANGE_MARKER}"); return result_from_remote(rc=rc, stdout=out, stderr=err, message="network.firewall.iptables.delete failed")

class IptablesExistsAssertPlugin(ReadOnlyCommandPlugin):
    name="network.firewall.iptables.exists_assert"; description="Assert an iptables rule exists."; required_params=("chain","rule"); optional_params=("table","ipv6","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        binary="ip6tables" if bool(params.get("ipv6",False)) else "iptables"; table=str(params.get("table","filter")); return [f"{sudo_prefix(params, default=True)}{binary} -t {quote(table)} -C {quote(params['chain'])} {params['rule']}"]

class IptablesCounterAssertPlugin(ReadOnlyCommandPlugin):
    name="network.firewall.iptables.counter_assert"; description="Assert iptables chain packet counters are above a threshold."; required_params=("chain",); optional_params=("table","min_packets","ipv6","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]:
        binary="ip6tables" if bool(params.get("ipv6",False)) else "iptables"; table=str(params.get("table","filter")); minp=int(params.get("min_packets",1)); return [f"{sudo_prefix(params, default=True)}{binary} -t {quote(table)} -L {quote(params['chain'])} -v -n -x | awk 'NR>2 && $1+0>={minp} {{found=1}} END {{exit !found}}'"]

class UfwDeletePlugin(BasePlugin):
    name="network.firewall.ufw.delete"; description="Delete a UFW rule after explicit confirmation."; required_params=("rule",); optional_params=("confirm","sudo"); opens_remote_session=True
    def validate(self, params: Dict[str, Any])->None:
        super().validate(params)
        if not bool(params.get("confirm",False)): raise PluginValidationError("network.firewall.ufw.delete requires confirm=true")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: self.validate(params); return [f"{sudo_prefix(params, default=True)}ufw --force delete {params['rule']}"]
    def execute(self, params: Dict[str, Any], context: ExecutionContext)->PluginResult:
        rc,out,err=exec_remote(context,self.manual_commands(params,context)[0]+f" && echo {CHANGE_MARKER}"); return result_from_remote(rc=rc, stdout=out, stderr=err, message="network.firewall.ufw.delete failed")

class UfwResetPlugin(UfwDeletePlugin):
    name="network.firewall.ufw.reset"; description="Reset UFW after explicit confirmation."; required_params=(); optional_params=("confirm","sudo")
    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext)->list[str]: self.validate(params); return [f"{sudo_prefix(params, default=True)}ufw --force reset"]

# Parameter schema disambiguation for names that have plugin-specific meaning.
for _cls in (UserFactsPlugin, UserShellAssertPlugin, UserHomeAssertPlugin, UserGroupsAssertPlugin, SudoListPlugin, SudoAssertPlugin, SudoCanRunPlugin):
    _cls.parameter_schema = {"user": {"type": "string", "description": "User account name."}}
UserShellAssertPlugin.parameter_schema = {"user": {"type": "string", "description": "User account name."}, "shell": {"type": "string", "description": "Expected login shell."}}
GroupMembersPlugin.parameter_schema = {"group": {"type": "string", "description": "Group name."}}
GroupMemberAbsentPlugin.parameter_schema = {"user": {"type": "string", "description": "User account name."}, "group": {"type": "string", "description": "Group name."}}
