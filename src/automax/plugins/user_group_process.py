# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote user, group and process management plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


class GroupCreatePlugin(BasePlugin):
    """Create a group if it does not already exist."""

    name = "group.create"
    description = "Create a remote group."
    required_params = ("name",)
    optional_params = ("gid", "system", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        flags = []
        if bool(params.get("system", False)):
            flags.append("--system")
        if params.get("gid") is not None:
            flags.extend(["--gid", quote(params["gid"])])
        command = (
            f"getent group {quote(params['name'])} >/dev/null "
            f"|| {{ {sudo_prefix(params, default=True)}groupadd {' '.join(flags)} {quote(params['name'])} "
            f"&& echo {CHANGE_MARKER}; }}"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="group.create failed")


class GroupRemovePlugin(BasePlugin):
    """Remove a group if it exists."""

    name = "group.remove"
    description = "Remove a remote group."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        command = (
            f"if getent group {quote(params['name'])} >/dev/null; then "
            f"{sudo_prefix(params, default=True)}groupdel {quote(params['name'])} && echo {CHANGE_MARKER}; fi"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="group.remove failed")


class UserCreatePlugin(BasePlugin):
    """Create a user if it does not already exist."""

    name = "user.create"
    description = "Create a remote user."
    required_params = ("name",)
    optional_params = (
        "uid",
        "group",
        "groups",
        "system",
        "shell",
        "home",
        "create_home",
        "comment",
        "sudo",
    )
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        flags = []
        if bool(params.get("system", False)):
            flags.append("--system")
        if params.get("uid") is not None:
            flags.extend(["--uid", quote(params["uid"])])
        if params.get("group"):
            flags.extend(["--gid", quote(params["group"])])
        groups = _list(params.get("groups"))
        if groups:
            flags.extend(["--groups", quote(",".join(groups))])
        if params.get("shell"):
            flags.extend(["--shell", quote(params["shell"])])
        if params.get("home"):
            flags.extend(["--home-dir", quote(params["home"])])
        if "create_home" in params:
            flags.append("--create-home" if bool(params.get("create_home")) else "--no-create-home")
        if params.get("comment"):
            flags.extend(["--comment", quote(params["comment"])])
        command = (
            f"id -u {quote(params['name'])} >/dev/null 2>&1 "
            f"|| {{ {sudo_prefix(params, default=True)}useradd {' '.join(flags)} {quote(params['name'])} "
            f"&& echo {CHANGE_MARKER}; }}"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="user.create failed")


class UserModifyPlugin(BasePlugin):
    """Modify an existing user."""

    name = "user.modify"
    description = "Modify a remote user."
    required_params = ("name",)
    optional_params = ("uid", "group", "groups", "append", "shell", "home", "comment", "lock", "unlock", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        flags = []
        if params.get("uid") is not None:
            flags.extend(["--uid", quote(params["uid"])])
        if params.get("group"):
            flags.extend(["--gid", quote(params["group"])])
        groups = _list(params.get("groups"))
        if groups:
            if bool(params.get("append", False)):
                flags.append("--append")
            flags.extend(["--groups", quote(",".join(groups))])
        if params.get("shell"):
            flags.extend(["--shell", quote(params["shell"])])
        if params.get("home"):
            flags.extend(["--home", quote(params["home"])])
        if params.get("comment"):
            flags.extend(["--comment", quote(params["comment"])])
        if bool(params.get("lock", False)) and bool(params.get("unlock", False)):
            raise PluginValidationError("user.modify cannot set both lock and unlock")
        if bool(params.get("lock", False)):
            flags.append("--lock")
        if bool(params.get("unlock", False)):
            flags.append("--unlock")
        if not flags:
            return PluginResult.success(changed=False, message="no user.modify fields requested")
        command = (
            f"id -u {quote(params['name'])} >/dev/null 2>&1 && "
            f"{sudo_prefix(params, default=True)}usermod {' '.join(flags)} {quote(params['name'])} && echo {CHANGE_MARKER}"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="user.modify failed")


class UserRemovePlugin(BasePlugin):
    """Remove a user if it exists."""

    name = "user.remove"
    description = "Remove a remote user."
    required_params = ("name",)
    optional_params = ("remove_home", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        flag = "--remove" if bool(params.get("remove_home", False)) else ""
        command = (
            f"if id -u {quote(params['name'])} >/dev/null 2>&1; then "
            f"{sudo_prefix(params, default=True)}userdel {flag} {quote(params['name'])} && echo {CHANGE_MARKER}; fi"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="user.remove failed")


class ProcessKillPlugin(BasePlugin):
    """Kill a remote process by PID or pattern."""

    name = "process.kill"
    description = "Kill a remote process by PID or pattern."
    optional_params = ("pid", "pattern", "signal", "sudo", "ignore_missing")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        if bool(params.get("pid")) == bool(params.get("pattern")):
            raise PluginValidationError("process.kill requires exactly one of pid or pattern")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        signal = str(params.get("signal", "TERM"))
        ignore_missing = bool(params.get("ignore_missing", True))
        if params.get("pid"):
            command = f"{sudo_prefix(params, default=True)}kill -s {quote(signal)} {quote(params['pid'])} && echo {CHANGE_MARKER}"
        else:
            command = f"{sudo_prefix(params, default=True)}pkill -{quote(signal)} -f {quote(params['pattern'])} && echo {CHANGE_MARKER}"
        if ignore_missing:
            command = f"{command} || true"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="process.kill failed")


class ProcessWaitPlugin(BasePlugin):
    """Wait for a process to appear or disappear."""

    name = "process.wait"
    description = "Wait for a remote process state."
    optional_params = ("pid", "pattern", "state", "timeout", "interval", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        if bool(params.get("pid")) == bool(params.get("pattern")):
            raise PluginValidationError("process.wait requires exactly one of pid or pattern")
        if str(params.get("state", "present")) not in {"present", "absent"}:
            raise PluginValidationError("process.wait state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        timeout = int(params.get("timeout", 60))
        interval = int(params.get("interval", 2))
        state = str(params.get("state", "present"))
        if params.get("pid"):
            check = f"kill -0 {quote(params['pid'])} >/dev/null 2>&1"
        else:
            check = f"pgrep -f {quote(params['pattern'])} >/dev/null 2>&1"
        command = f"""
end=$((SECONDS + {timeout}))
while [ "$SECONDS" -le "$end" ]; do
  if {check}; then found=1; else found=0; fi
  if [ {quote(state)} = present ] && [ "$found" = 1 ]; then exit 0; fi
  if [ {quote(state)} = absent ] && [ "$found" = 0 ]; then exit 0; fi
  sleep {interval}
done
echo 'process.wait timed out' >&2
exit 1
"""
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="process.wait failed")
        return PluginResult.success(changed=False, stdout=out, stderr=err)

class ProcessSignalPlugin(BasePlugin):
    """Send a signal to a process by PID or pattern."""

    name = "process.signal"
    description = "Send a signal to a remote process by PID or pattern."
    optional_params = ("pid", "pattern", "signal", "sudo", "ignore_missing")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        if bool(params.get("pid")) == bool(params.get("pattern")):
            raise PluginValidationError("process.signal requires exactly one of pid or pattern")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "process.signal is a runtime process operation with no file diff"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        signal = str(params.get("signal", "TERM"))
        if params.get("pid"):
            command = f"{sudo_prefix(params, default=True)}kill -s {quote(signal)} {quote(params['pid'])}"
        else:
            command = f"{sudo_prefix(params, default=True)}pkill -{quote(signal)} -f {quote(params['pattern'])}"
        if bool(params.get("ignore_missing", True)):
            command += " || true"
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0] + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="process.signal failed")

class ProcessAssertAbsentPlugin(BasePlugin):
    """Assert no process matches a pattern."""

    name = "process.assert_absent"
    description = "Assert that no remote process matches a pattern."
    required_params = ("pattern",)
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "process.assert_absent is a read-only process assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"! {sudo_prefix(params, default=True)}pgrep -f {quote(params['pattern'])} >/dev/null"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="process.assert_absent failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)

class ProcessAssertCountPlugin(BasePlugin):
    """Assert process count for a pattern."""

    name = "process.assert_count"
    description = "Assert the number of remote processes matching a pattern."
    required_params = ("pattern",)
    optional_params = ("count", "min_count", "max_count", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not any(key in params for key in ("count", "min_count", "max_count")):
            raise PluginValidationError("process.assert_count requires count, min_count or max_count")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "process.assert_count is a read-only process count assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        checks = [f"actual=$({sudo_prefix(params, default=True)}pgrep -fc {quote(params['pattern'])})"]
        if params.get("count") is not None:
            checks.append(f"test \"$actual\" -eq {quote(params['count'])}")
        if params.get("min_count") is not None:
            checks.append(f"test \"$actual\" -ge {quote(params['min_count'])}")
        if params.get("max_count") is not None:
            checks.append(f"test \"$actual\" -le {quote(params['max_count'])}")
        return [" && ".join(checks)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="process.assert_count failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
