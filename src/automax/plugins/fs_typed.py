# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Type-strict filesystem resource plugins.
"""

from __future__ import annotations

import json
import posixpath
import time
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import (
    CHANGE_MARKER,
    apply_cwd,
    exec_remote,
    heredoc_to_stdin,
    quote,
    result_from_remote,
    sudo_command,
    sudo_shell_run_function,
)

_PROTECTED_DIR_PATHS = {
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/home",
    "/lib",
    "/lib64",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/srv",
    "/sys",
    "/tmp",
    "/usr",
    "/var",
}


def _clean_path(value: Any) -> str:
    raw = str(value).strip()
    if raw in {"", ".", ".."}:
        return raw
    if raw.startswith("/"):
        return posixpath.normpath(raw)
    return posixpath.normpath(raw)


def _bool_arg(value: Any) -> str:
    return str(bool(value)).lower()


def _int_param(params: Dict[str, Any], name: str, default: int, minimum: int) -> int:
    try:
        value = int(params.get(name, default))
    except (TypeError, ValueError) as exc:
        raise PluginValidationError(f"{name} must be an integer") from exc
    if value < minimum:
        raise PluginValidationError(f"{name} must be >= {minimum}")
    return value


def _interval(params: Dict[str, Any]) -> float:
    try:
        value = float(params.get("interval", 5))
    except (TypeError, ValueError) as exc:
        raise PluginValidationError("interval must be a number") from exc
    if value <= 0:
        raise PluginValidationError("interval must be greater than zero")
    return value


def _state(params: Dict[str, Any]) -> str:
    state = str(params.get("state", "present"))
    if state not in {"present", "absent"}:
        raise PluginValidationError("state must be present or absent")
    return state


def _type_status_script() -> str:
    return f"""
set -eu
path=$1
kind=$2
use_sudo=$3
{sudo_shell_run_function()}
exists_any() {{ run test -e "$path" || run test -L "$path"; }}
is_dir() {{ run test -d "$path" && ! run test -L "$path"; }}
is_file() {{ run test -f "$path" && ! run test -L "$path"; }}
is_symlink() {{ run test -L "$path"; }}
if ! exists_any; then
    echo absent
    exit 10
fi
if case "$kind" in
    dir) is_dir ;;
    file) is_file ;;
    symlink) is_symlink ;;
    *) echo "unsupported filesystem kind: $kind" >&2; exit 2 ;;
esac; then
    echo present
    exit 0
fi
echo "wrong-type: expected $kind at $path" >&2
exit 20
"""


def _type_status_command(kind: str, params: Dict[str, Any], context: ExecutionContext) -> str:
    command = heredoc_to_stdin(
        f"sh -s -- {quote(params['path'])} {quote(kind)} {quote(_bool_arg(params.get('sudo', False)))}",
        _type_status_script(),
        prefix="AUTOMAX_SH",
    )
    return apply_cwd(command, context, params.get("cwd"))


class _TypedFilesystemPlugin(BasePlugin):
    kind = "path"
    kind_label = "path"

    def _validate_path(self, params: Dict[str, Any], *, destructive: bool = False) -> None:
        path = _clean_path(params["path"])
        if path in {"", ".", ".."}:
            raise PluginValidationError(f"{self.name} path must not be empty, '.' or '..'")
        if destructive and self.kind == "dir" and path in _PROTECTED_DIR_PATHS:
            raise PluginValidationError(f"{self.name} refuses protected root-level directory: {path}")

    def _status(self, params: Dict[str, Any], context: ExecutionContext) -> tuple[int, str, str]:
        return exec_remote(
            context,
            _type_status_command(self.kind, params, context),
            get_pty=bool(params.get("sudo", False)),
        )


class _TypedExistsPlugin(_TypedFilesystemPlugin):
    required_params = ("path",)
    optional_params = ("sudo", "cwd")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params)
        if context.ssh_client is None:
            return PluginResult.failure(message=f"{self.name} requires an SSH session")
        rc, out, err = self._status(params, context)
        if rc == 0:
            return PluginResult.success(
                changed=False,
                rc=0,
                stdout=out,
                data={"exists": True, "path": params["path"], "type": self.kind},
            )
        if rc == 10:
            return PluginResult.success(
                changed=False,
                rc=0,
                stdout=out,
                data={"exists": False, "path": params["path"], "type": self.kind},
            )
        return PluginResult.failure(rc=rc, stdout=out, stderr=err, message=f"{self.name} failed")


class _TypedWaitPlugin(_TypedFilesystemPlugin):
    required_params = ("path",)
    optional_params = ("state", "retries", "interval", "sudo", "cwd")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params)
        if context.ssh_client is None:
            return PluginResult.failure(message=f"{self.name} requires an SSH session")
        state = _state(params)
        retries = _int_param(params, "retries", 12, 1)
        interval = _interval(params)
        last_rc = 1
        last_out = ""
        last_err = ""
        for attempt in range(1, retries + 1):
            last_rc, last_out, last_err = self._status(params, context)
            if state == "present" and last_rc == 0:
                return PluginResult.success(
                    changed=False,
                    rc=0,
                    stdout=last_out,
                    message=f"{self.kind_label} is present",
                    data={"path": params["path"], "state": state, "type": self.kind, "attempts": attempt},
                )
            if state == "absent" and last_rc == 10:
                return PluginResult.success(
                    changed=False,
                    rc=0,
                    stdout=last_out,
                    message=f"{self.kind_label} is absent",
                    data={"path": params["path"], "state": state, "type": self.kind, "attempts": attempt},
                )
            if last_rc == 20:
                return PluginResult.failure(
                    rc=last_rc,
                    stdout=last_out,
                    stderr=last_err,
                    message=f"{self.name} found a different filesystem type",
                )
            if attempt < retries:
                time.sleep(interval)
        return PluginResult.failure(
            rc=last_rc,
            stdout=last_out,
            stderr=last_err,
            message=f"{self.name} retries exhausted",
            data={"path": params["path"], "state": state, "type": self.kind, "attempts": retries},
        )


class FsDirCreatePlugin(_TypedFilesystemPlugin):
    """Create a real directory and refuse symlink masquerading."""

    name = "fs.dir.create"
    description = "Create a real directory, refusing files and symlinks at the destination."
    kind = "dir"
    kind_label = "directory"
    required_params = ("path",)
    optional_params = ("mode", "owner", "group", "sudo", "cwd")
    opens_remote_session = True

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        script = f"""
set -eu
path=$1
mode=$2
owner=$3
group=$4
use_sudo=$5
{sudo_shell_run_function()}
exists_any() {{ run test -e "$path" || run test -L "$path"; }}
is_dir() {{ run test -d "$path" && ! run test -L "$path"; }}
changed=false
if exists_any; then
    if ! is_dir; then
        echo "refusing to create directory over non-directory or symlink: $path" >&2
        exit 1
    fi
else
    run mkdir -p -- "$path"
    changed=true
fi
if [ -n "$mode" ] && [ "$(run stat -c %a "$path")" != "$mode" ]; then
    run chmod "$mode" "$path"
    changed=true
fi
if [ -n "$owner$group" ]; then
    owner_group="$owner:$group"
    current_owner=$(run stat -c %U "$path")
    current_group=$(run stat -c %G "$path")
    if [ -n "$owner" ] && [ "$current_owner" != "$owner" ] || [ -n "$group" ] && [ "$current_group" != "$group" ]; then
        run chown "$owner_group" "$path"
        changed=true
    fi
fi
if [ "$changed" = "true" ]; then
    echo {CHANGE_MARKER}
fi
"""
        command = heredoc_to_stdin(
            f"sh -s -- {quote(params['path'])} {quote(params.get('mode', ''))} "
            f"{quote(params.get('owner', ''))} {quote(params.get('group', ''))} "
            f"{quote(_bool_arg(params.get('sudo', False)))}",
            script,
            prefix="AUTOMAX_SH",
        )
        return apply_cwd(command, context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        self._validate_path(params)
        return [self._command(params, context)]

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params)
        return PluginResult.success(
            changed=False,
            message=f"dry-run: create directory {params.get('path')}",
            data={"params": params, "commands": self.manual_commands(params, context)},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="fs.dir.create requires an SSH session")
        rc, out, err = exec_remote(context, self._command(params, context), get_pty=bool(params.get("sudo", False)))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.dir.create failed",
            data={"path": params["path"]},
        )


class FsFileCreatePlugin(FsDirCreatePlugin):
    """Create a real regular file and refuse directories and symlinks."""

    name = "fs.file.create"
    description = "Create a real regular file, refusing directories and symlinks at the destination."
    kind = "file"
    kind_label = "file"

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        script = f"""
set -eu
path=$1
mode=$2
owner=$3
group=$4
use_sudo=$5
{sudo_shell_run_function()}
exists_any() {{ run test -e "$path" || run test -L "$path"; }}
is_file() {{ run test -f "$path" && ! run test -L "$path"; }}
changed=false
if exists_any; then
    if ! is_file; then
        echo "refusing to create file over non-file or symlink: $path" >&2
        exit 1
    fi
else
    run touch -- "$path"
    changed=true
fi
if [ -n "$mode" ] && [ "$(run stat -c %a "$path")" != "$mode" ]; then
    run chmod "$mode" "$path"
    changed=true
fi
if [ -n "$owner$group" ]; then
    owner_group="$owner:$group"
    current_owner=$(run stat -c %U "$path")
    current_group=$(run stat -c %G "$path")
    if [ -n "$owner" ] && [ "$current_owner" != "$owner" ] || [ -n "$group" ] && [ "$current_group" != "$group" ]; then
        run chown "$owner_group" "$path"
        changed=true
    fi
fi
if [ "$changed" = "true" ]; then
    echo {CHANGE_MARKER}
fi
"""
        command = heredoc_to_stdin(
            f"sh -s -- {quote(params['path'])} {quote(params.get('mode', ''))} "
            f"{quote(params.get('owner', ''))} {quote(params.get('group', ''))} "
            f"{quote(_bool_arg(params.get('sudo', False)))}",
            script,
            prefix="AUTOMAX_SH",
        )
        return apply_cwd(command, context, params.get("cwd"))

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params, destructive=True)
        return PluginResult.success(
            changed=False,
            message=f"dry-run: create file {params.get('path')}",
            data={"params": params, "commands": self.manual_commands(params, context)},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        result = super().execute(params, context)
        if result.message == "fs.dir.create requires an SSH session":
            return PluginResult.failure(message="fs.file.create requires an SSH session")
        if not result.ok and result.message == "fs.dir.create failed":
            result.message = "fs.file.create failed"
        return result


class _TypedRemovePlugin(_TypedFilesystemPlugin):
    required_params = ("path",)
    optional_params = ("sudo", "cwd")
    opens_remote_session = True
    recursive_capable = False

    def _remove_command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        recursive_arg = _bool_arg(params.get("recursive", False))
        script = f"""
set -eu
path=$1
kind=$2
recursive=$3
use_sudo=$4
{sudo_shell_run_function()}
exists_any() {{ run test -e "$path" || run test -L "$path"; }}
is_dir() {{ run test -d "$path" && ! run test -L "$path"; }}
is_file() {{ run test -f "$path" && ! run test -L "$path"; }}
is_symlink() {{ run test -L "$path"; }}
if ! exists_any; then
    exit 0
fi
if ! case "$kind" in
    dir) is_dir ;;
    file) is_file ;;
    symlink) is_symlink ;;
    *) echo "unsupported filesystem kind: $kind" >&2; exit 2 ;;
esac; then
    echo "refusing to remove non-$kind path: $path" >&2
    exit 1
fi
case "$kind" in
    dir)
        if [ "$recursive" = "true" ]; then
            run rm -rf -- "$path"
        else
            run rmdir -- "$path"
        fi
        ;;
    file) run rm -f -- "$path" ;;
    symlink) run rm -f -- "$path" ;;
esac
echo {CHANGE_MARKER}
"""
        command = heredoc_to_stdin(
            f"sh -s -- {quote(params['path'])} {quote(self.kind)} {quote(recursive_arg)} "
            f"{quote(_bool_arg(params.get('sudo', False)))}",
            script,
            prefix="AUTOMAX_SH",
        )
        return apply_cwd(command, context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        self._validate_path(params, destructive=True)
        return [self._remove_command(params, context)]

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params, destructive=True)
        return PluginResult.success(
            changed=False,
            message=f"dry-run: remove {self.kind_label} {params.get('path')}",
            data={"params": params, "commands": self.manual_commands(params, context)},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params, destructive=True)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message=f"{self.name} requires an SSH session")
        rc, out, err = exec_remote(context, self._remove_command(params, context), get_pty=bool(params.get("sudo", False)))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message=f"{self.name} failed",
            data={"path": params["path"]},
        )


class FsDirRemovePlugin(_TypedRemovePlugin):
    """Remove a real directory and refuse files and symlinks."""

    name = "fs.dir.remove"
    description = "Remove a real directory, refusing files and symlinks. Non-empty directories require recursive=true."
    kind = "dir"
    kind_label = "directory"
    optional_params = ("recursive", "sudo", "cwd")
    recursive_capable = True


class FsFileRemovePlugin(_TypedRemovePlugin):
    """Remove a real regular file and refuse directories and symlinks."""

    name = "fs.file.remove"
    description = "Remove a real regular file, refusing directories and symlinks."
    kind = "file"
    kind_label = "file"


_SYMLINK_STATUS_SCRIPT = r'''
import json
import os
import stat
import sys

path = sys.argv[1]
expected_target = sys.argv[2] or None

def actual_type_for(path: str) -> str:
    try:
        mode = os.lstat(path).st_mode
    except OSError:
        return "unknown"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISCHR(mode):
        return "char-device"
    if stat.S_ISBLK(mode):
        return "block-device"
    if stat.S_ISFIFO(mode):
        return "fifo"
    if stat.S_ISSOCK(mode):
        return "socket"
    return "other"

data = {"path": path}
if expected_target is not None:
    data["expected_target"] = expected_target

if not os.path.lexists(path):
    data.update({"exists": False, "is_symlink": False})
    print(json.dumps(data, sort_keys=True))
    sys.exit(10)

if not os.path.islink(path):
    data.update({"exists": True, "is_symlink": False, "actual_type": actual_type_for(path)})
    print(json.dumps(data, sort_keys=True))
    sys.exit(20)

target = os.readlink(path)
resolved_target = target if os.path.isabs(target) else os.path.normpath(os.path.join(os.path.dirname(path), target))
target_exists = os.path.exists(resolved_target)
data.update(
    {
        "exists": True,
        "is_symlink": True,
        "target": target,
        "resolved_target": resolved_target,
        "target_exists": target_exists,
        "broken": not target_exists,
    }
)
if expected_target is not None:
    data["matches"] = target == expected_target
print(json.dumps(data, sort_keys=True))
'''


def _symlink_status_command(params: Dict[str, Any], context: ExecutionContext) -> str:
    python = sudo_command(params, "python3", default=False)
    command = heredoc_to_stdin(
        f"{python} - {quote(params['path'])} {quote(params.get('target', ''))}",
        _SYMLINK_STATUS_SCRIPT,
        prefix="AUTOMAX_PY",
    )
    return apply_cwd(command, context, params.get("cwd"))


def _parse_symlink_status(stdout: str) -> Dict[str, Any]:
    return json.loads(stdout.strip() or "{}")


class FsDirCheckPlugin(_TypedExistsPlugin):
    """Check whether a real directory exists."""

    name = "fs.dir.check"
    description = "Check whether a real directory exists, failing if another path type exists there."
    kind = "dir"
    kind_label = "directory"


class FsFileCheckPlugin(_TypedExistsPlugin):
    """Check whether a real regular file exists."""

    name = "fs.file.check"
    description = "Check whether a real regular file exists, failing if another path type exists there."
    kind = "file"
    kind_label = "file"


class FsSymlinkCheckPlugin(_TypedFilesystemPlugin):
    """Check whether a symlink exists and optionally matches a literal target."""

    name = "fs.symlink.check"
    description = "Check whether a symlink exists and optionally whether it points to a target."
    kind = "symlink"
    kind_label = "symlink"
    required_params = ("path",)
    optional_params = ("target", "sudo", "cwd")
    opens_remote_session = True
    supports_check_mode = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params)
        if context.ssh_client is None:
            return PluginResult.failure(message=f"{self.name} requires an SSH session")
        rc, out, err = exec_remote(
            context,
            _symlink_status_command(params, context),
            get_pty=bool(params.get("sudo", False)),
        )
        try:
            data = _parse_symlink_status(out)
        except json.JSONDecodeError as exc:
            return PluginResult.failure(rc=1, stdout=out, stderr=str(exc), message="fs.symlink.check could not parse status output")
        if rc in {0, 10}:
            if "target" in params and "matches" not in data:
                data["matches"] = False
            return PluginResult.success(changed=False, rc=0, stdout=out, stderr=err, data=data)
        if rc == 20:
            return PluginResult.failure(
                rc=rc,
                stdout=out,
                stderr=err,
                message="fs.symlink.check found a different filesystem type",
                data=data,
            )
        return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.symlink.check failed", data=data)


class FsSymlinkGetPlugin(_TypedFilesystemPlugin):
    """Read symlink target state without treating non-symlinks as check failures."""

    name = "fs.symlink.get"
    description = "Read symlink target, resolved target and broken-link state."
    kind = "symlink"
    kind_label = "symlink"
    required_params = ("path",)
    optional_params = ("sudo", "cwd")
    opens_remote_session = True
    supports_check_mode = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        self._validate_path(params)
        if context.ssh_client is None:
            return PluginResult.failure(message=f"{self.name} requires an SSH session")
        rc, out, err = exec_remote(
            context,
            _symlink_status_command(params, context),
            get_pty=bool(params.get("sudo", False)),
        )
        try:
            data = _parse_symlink_status(out)
        except json.JSONDecodeError as exc:
            return PluginResult.failure(rc=1, stdout=out, stderr=str(exc), message="fs.symlink.get could not parse status output")
        if rc in {0, 10, 20}:
            return PluginResult.success(changed=False, rc=0, stdout=out, stderr=err, data=data)
        return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.symlink.get failed", data=data)


class FsDirWaitPlugin(_TypedWaitPlugin):
    """Wait until a real directory condition is true."""

    name = "fs.dir.wait"
    description = "Wait for a real directory to become present or absent."
    kind = "dir"
    kind_label = "directory"


class FsFileWaitPlugin(_TypedWaitPlugin):
    """Wait until a real regular file condition is true."""

    name = "fs.file.wait"
    description = "Wait for a real regular file to become present or absent."
    kind = "file"
    kind_label = "file"


class FsSymlinkWaitPlugin(_TypedWaitPlugin):
    """Wait until a symbolic link condition is true."""

    name = "fs.symlink.wait"
    description = "Wait for a symbolic link to become present or absent."
    kind = "symlink"
    kind_label = "symlink"
