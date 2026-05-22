"""
Remote wait and assert plugins.

wait.* plugins poll until a condition becomes true or timeout expires.
assert.* plugins evaluate once and fail immediately when the condition is false.
"""

from __future__ import annotations

import socket
import time
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import exec_remote, quote


def _timeout(params: Dict[str, Any], default: int = 60) -> int:
    value = int(params.get("timeout", default))
    if value < 1:
        raise PluginValidationError("timeout must be greater than zero")
    return value


def _interval(params: Dict[str, Any], default: int = 2) -> float:
    value = float(params.get("interval", default))
    if value <= 0:
        raise PluginValidationError("interval must be greater than zero")
    return value


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", False)) else ""


def _tcp_check(host: str, port: int, timeout: float) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, ""
    except OSError as exc:
        return False, str(exc)


def _expected_match(params: Dict[str, Any], stdout: str, rc: int) -> bool:
    if "rc" in params and rc != int(params["rc"]):
        return False
    if "equals" in params and stdout.strip() != str(params["equals"]):
        return False
    if "contains" in params and str(params["contains"]) not in stdout:
        return False
    if "not_contains" in params and str(params["not_contains"]) in stdout:
        return False
    return True


def _path_test_command(params: Dict[str, Any]) -> str:
    state = str(params.get("state", "present"))
    path_type = str(params.get("type", "path"))
    if state not in {"present", "absent"}:
        raise PluginValidationError("state must be present or absent")
    flags = {
        "path": "-e",
        "any": "-e",
        "file": "-f",
        "directory": "-d",
        "dir": "-d",
        "symlink": "-L",
    }
    flag = flags.get(path_type)
    if flag is None:
        raise PluginValidationError("type must be path, any, file, directory, dir or symlink")
    test = f"test {flag} {quote(params['path'])}"
    return test if state == "present" else f"! {test}"


class WaitTcpPlugin(BasePlugin):
    """Wait until a TCP endpoint is reachable from the controller."""

    name = "wait.tcp"
    description = "Wait until a TCP host/port is reachable from the controller."
    required_params = ("host", "port")
    optional_params = ("timeout", "interval", "connect_timeout")
    opens_remote_session = False

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        timeout = _timeout(params)
        interval = _interval(params)
        connect_timeout = float(params.get("connect_timeout", 3))
        deadline = time.monotonic() + timeout
        last_error = ""
        while time.monotonic() <= deadline:
            ok, last_error = _tcp_check(str(params["host"]), int(params["port"]), connect_timeout)
            if ok:
                return PluginResult.success(
                    changed=False,
                    message="TCP endpoint is reachable",
                    data={"host": params["host"], "port": int(params["port"])},
                )
            time.sleep(interval)
        return PluginResult.failure(
            message="wait.tcp timed out",
            stderr=last_error,
            data={"host": params["host"], "port": int(params["port"])},
        )


class AssertTcpPlugin(BasePlugin):
    """Assert that a TCP endpoint is reachable from the controller."""

    name = "assert.tcp"
    description = "Assert that a TCP host/port is reachable from the controller."
    required_params = ("host", "port")
    optional_params = ("connect_timeout",)
    opens_remote_session = False

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        ok, error = _tcp_check(
            str(params["host"]),
            int(params["port"]),
            float(params.get("connect_timeout", 3)),
        )
        if not ok:
            return PluginResult.failure(
                message="assert.tcp failed",
                stderr=error,
                data={"host": params["host"], "port": int(params["port"])},
            )
        return PluginResult.success(
            changed=False,
            message="TCP endpoint is reachable",
            data={"host": params["host"], "port": int(params["port"])},
        )


class WaitCommandPlugin(BasePlugin):
    """Wait until a remote command matches rc/stdout expectations."""

    name = "wait.command"
    description = "Wait until a remote command matches the requested condition."
    required_params = ("command",)
    optional_params = (
        "timeout",
        "interval",
        "rc",
        "equals",
        "contains",
        "not_contains",
        "sudo",
        "get_pty",
    )
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        timeout = _timeout(params)
        interval = _interval(params)
        deadline = time.monotonic() + timeout
        last_rc = 1
        last_out = ""
        last_err = ""
        command = f"{_sudo(params)}{params['command']}"
        while time.monotonic() <= deadline:
            last_rc, last_out, last_err = exec_remote(
                context,
                command,
                get_pty=bool(params.get("get_pty", params.get("sudo", False))),
            )
            if _expected_match(params, last_out, last_rc):
                return PluginResult.success(
                    changed=False,
                    rc=last_rc,
                    stdout=last_out,
                    stderr=last_err,
                    message="command condition matched",
                )
            time.sleep(interval)
        return PluginResult.failure(
            rc=last_rc,
            stdout=last_out,
            stderr=last_err,
            message="wait.command timed out",
        )


class AssertCommandPlugin(BasePlugin):
    """Assert that a remote command matches rc/stdout expectations."""

    name = "assert.command"
    description = "Assert that a remote command matches the requested condition."
    required_params = ("command",)
    optional_params = ("rc", "equals", "contains", "not_contains", "sudo", "get_pty")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(
            context,
            f"{_sudo(params)}{params['command']}",
            get_pty=bool(params.get("get_pty", params.get("sudo", False))),
        )
        if not _expected_match(params, out, rc):
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="assert.command failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class WaitFilePlugin(BasePlugin):
    """Wait until a remote file condition is true."""

    name = "wait.file"
    description = "Wait until a remote file condition is true."
    required_params = ("path",)
    optional_params = ("state", "type", "timeout", "interval", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        params = {**params, "type": params.get("type", "file")}
        timeout = _timeout(params)
        interval = _interval(params)
        command = f"{_sudo(params)}{_path_test_command(params)}"
        deadline = time.monotonic() + timeout
        last_rc = 1
        last_err = ""
        while time.monotonic() <= deadline:
            last_rc, _, last_err = exec_remote(context, command, get_pty=bool(params.get("sudo", False)))
            if last_rc == 0:
                return PluginResult.success(
                    changed=False,
                    message="file condition matched",
                    data={"path": params["path"], "state": params.get("state", "present")},
                )
            time.sleep(interval)
        return PluginResult.failure(rc=last_rc, stderr=last_err, message="wait.file timed out")


class AssertFilePlugin(BasePlugin):
    """Assert that a remote file condition is true."""

    name = "assert.file"
    description = "Assert that a remote file condition is true."
    required_params = ("path",)
    optional_params = ("state", "type", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        params = {**params, "type": params.get("type", "file")}
        rc, out, err = exec_remote(
            context,
            f"{_sudo(params)}{_path_test_command(params)}",
            get_pty=bool(params.get("sudo", False)),
        )
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="assert.file failed")
        return PluginResult.success(
            changed=False,
            data={"path": params["path"], "state": params.get("state", "present")},
        )


class WaitPathPlugin(WaitFilePlugin):
    """Wait until a remote path condition is true."""

    name = "wait.path"
    description = "Wait until a remote path condition is true."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return super().execute({**params, "type": params.get("type", "path")}, context)


class AssertPathPlugin(AssertFilePlugin):
    """Assert that a remote path condition is true."""

    name = "assert.path"
    description = "Assert that a remote path condition is true."

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return super().execute({**params, "type": params.get("type", "path")}, context)


class WaitProcessPlugin(BasePlugin):
    """Wait until a process matching a pattern is present or absent."""

    name = "wait.process"
    description = "Wait until a remote process condition is true."
    required_params = ("pattern",)
    optional_params = ("state", "timeout", "interval", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("state must be present or absent")
        timeout = _timeout(params)
        interval = _interval(params)
        command = f"{_sudo(params)}pgrep -f {quote(params['pattern'])} >/dev/null"
        if state == "absent":
            command = f"! {command}"
        deadline = time.monotonic() + timeout
        last_rc = 1
        last_err = ""
        while time.monotonic() <= deadline:
            last_rc, _, last_err = exec_remote(context, command, get_pty=bool(params.get("sudo", False)))
            if last_rc == 0:
                return PluginResult.success(
                    changed=False,
                    message="process condition matched",
                    data={"pattern": params["pattern"], "state": state},
                )
            time.sleep(interval)
        return PluginResult.failure(rc=last_rc, stderr=last_err, message="wait.process timed out")


class AssertDiskPlugin(BasePlugin):
    """Assert disk capacity thresholds for a remote filesystem path."""

    name = "assert.disk"
    description = "Assert remote disk capacity thresholds."
    required_params = ("path",)
    optional_params = ("min_free_mb", "min_free_percent", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if "min_free_mb" not in params and "min_free_percent" not in params:
            raise PluginValidationError("assert.disk requires min_free_mb or min_free_percent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        command = f"{_sudo(params)}df -Pk {quote(params['path'])} | awk 'NR==2 {{print $2, $4}}'"
        rc, out, err = exec_remote(context, command, get_pty=bool(params.get("sudo", False)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="assert.disk failed")
        try:
            total_kb, free_kb = [int(item) for item in out.strip().split()[:2]]
        except (ValueError, IndexError) as exc:
            return PluginResult.failure(
                rc=1,
                stdout=out,
                stderr=str(exc),
                message="assert.disk could not parse df output",
            )
        free_mb = free_kb // 1024
        free_percent = (free_kb / total_kb * 100.0) if total_kb else 0.0
        if "min_free_mb" in params and free_mb < int(params["min_free_mb"]):
            return PluginResult.failure(
                message="assert.disk free MB threshold failed",
                data={"free_mb": free_mb, "free_percent": free_percent},
            )
        if "min_free_percent" in params and free_percent < float(params["min_free_percent"]):
            return PluginResult.failure(
                message="assert.disk free percent threshold failed",
                data={"free_mb": free_mb, "free_percent": free_percent},
            )
        return PluginResult.success(
            changed=False,
            data={"free_mb": free_mb, "free_percent": free_percent},
        )
