# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote account access management plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file, upload_text_to_temp
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_stdin, quote, result_from_remote, sudo_prefix



class UserCheckPlugin(BasePlugin):
    """Check whether a remote user exists."""

    name = "identity.user.check"
    description = "Check whether a remote user exists."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(context, f"id -u {quote(params['name'])} >/dev/null 2>&1")
        return PluginResult.success(
            changed=False,
            rc=0,
            stdout="",
            stderr="" if rc == 0 else err,
            data={"name": params["name"], "exists": rc == 0},
        )


class GroupCheckPlugin(BasePlugin):
    """Check whether a remote group exists."""

    name = "identity.group.check"
    description = "Check whether a remote group exists."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(context, f"getent group {quote(params['name'])} >/dev/null")
        return PluginResult.success(
            changed=False,
            rc=0,
            stdout=out,
            stderr="" if rc == 0 else err,
            data={"name": params["name"], "exists": rc == 0},
        )


class UserLockPlugin(BasePlugin):
    """Lock a remote user account."""

    name = "identity.user.lock"
    description = "Lock a remote user account."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        name = quote(params["name"])
        command = (
            f"id -u {name} >/dev/null 2>&1 && "
            f"if passwd -S {name} 2>/dev/null | awk '{{print $2}}' | grep -Eq '^(L|LK|NP)$'; then "
            f"true; else {sudo_prefix(params, default=True)}usermod --lock {name} && echo {CHANGE_MARKER}; fi"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="identity.user.lock failed")


class UserUnlockPlugin(BasePlugin):
    """Unlock a remote user account."""

    name = "identity.user.unlock"
    description = "Unlock a remote user account."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        name = quote(params["name"])
        command = (
            f"id -u {name} >/dev/null 2>&1 && "
            f"if passwd -S {name} 2>/dev/null | awk '{{print $2}}' | grep -Eq '^(P|PS)$'; then "
            f"true; else {sudo_prefix(params, default=True)}usermod --unlock {name} && echo {CHANGE_MARKER}; fi"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="identity.user.unlock failed")


class UserPasswordSetPlugin(BasePlugin):
    """Set a remote user's password using either a password hash or plaintext value."""

    name = "identity.user.password.set"
    description = "Set a remote user's password using a password hash or plaintext value."
    required_params = ("name",)
    optional_params = ("password_hash", "password", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if bool(params.get("password_hash")) == bool(params.get("password")):
            raise PluginValidationError("identity.user.password.set requires exactly one of password_hash or password")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        name = str(params["name"])
        if params.get("password_hash"):
            # usermod --password expects a crypt(3) hash. The shell-quoted value is still sensitive,
            # but avoids sending plaintext passwords to the remote chpasswd process.
            command = f"id -u {quote(name)} >/dev/null 2>&1 && {sudo_prefix(params, default=True)}usermod --password {quote(params['password_hash'])} {quote(name)} && echo {CHANGE_MARKER}"
        else:
            temp_path = upload_text_to_temp(context, f"{name}:{params['password']}\n")
            command = f"{sudo_prefix(params, default=True)}chpasswd < {quote(temp_path)} && rm -f {quote(temp_path)} && echo {CHANGE_MARKER}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="identity.user.password.set failed")


class UserPasswordExpirePlugin(BasePlugin):
    """Expire a remote user's password to force a password change at next login."""

    name = "identity.user.password.expire"
    description = "Expire a remote user's password so it must be changed at next login."
    required_params = ("name",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        name = str(params["name"])
        prefix = sudo_prefix(params, default=True)
        command = (
            f"id -u {quote(name)} >/dev/null 2>&1 && "
            f"last_change=$({prefix}getent shadow {quote(name)} | cut -d: -f3) && "
            f'if [ "$last_change" = 0 ]; then true; '
            f"else {prefix}chage -d 0 {quote(name)} && echo {CHANGE_MARKER}; fi"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="identity.user.password.expire failed",
            data={"name": name, "expired": rc == 0},
        )


class SshAuthorizedKeyPlugin(BasePlugin):
    """Manage one line in a remote user's authorized_keys file."""

    name = "security.ssh.authorized_key.add"
    description = "Ensure an SSH authorized key is present or absent for a remote user."
    required_params = ("user", "key")
    optional_params = ("state", "sudo")
    parameter_schema = {
        "user": {"type": "string", "description": "Remote user account owning authorized_keys."},
        "key": {"type": "string", "description": "Authorized key line to manage."},
    }
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if str(params.get("state", "present")) not in {"present", "absent"}:
            raise PluginValidationError("security.ssh.authorized_key.add state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        user = str(params["user"])
        key = str(params["key"])
        state = str(params.get("state", "present"))
        script = r'''
set -eu
user=$1
key=$2
state=$3
home=$(getent passwd "$user" | cut -d: -f6)
if [ -z "$home" ]; then
  echo "user not found: $user" >&2
  exit 1
fi
ssh_dir="$home/.ssh"
auth_file="$ssh_dir/authorized_keys"
mkdir -p "$ssh_dir"
touch "$auth_file"
chmod 700 "$ssh_dir"
chmod 600 "$auth_file"
if [ "$state" = present ]; then
  if grep -Fqx -- "$key" "$auth_file"; then
    exit 0
  fi
  printf '%s\n' "$key" >> "$auth_file"
  echo __AUTOMAX_CHANGED__
else
  tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
  grep -Fxv -- "$key" "$auth_file" > "$tmp" || true
  if cmp -s "$tmp" "$auth_file"; then
    rm -f "$tmp"
    exit 0
  fi
  cat "$tmp" > "$auth_file"
  rm -f "$tmp"
  echo __AUTOMAX_CHANGED__
fi
chown -R "$user":"$user" "$ssh_dir" 2>/dev/null || true
'''
        prefix = sudo_prefix(params, default=True)
        command = heredoc_to_stdin(
            f"{prefix}sh -s -- {quote(user)} {quote(key)} {quote(state)}",
            script,
            prefix="AUTOMAX_SH",
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.ssh.authorized_key.add failed")


class SudoersDropinPlugin(BasePlugin):
    """Install or remove a sudoers drop-in file with optional visudo validation."""

    name = "security.sudo.dropin"
    description = "Install or remove a sudoers drop-in file with visudo validation."
    required_params = ("name",)
    optional_params = ("content", "state", "mode", "validate", "sudo")
    parameter_schema = {
        "name": {"type": "string", "description": "Drop-in filename under /etc/sudoers.d."},
        "content": {"type": "string", "description": "sudoers content installed when state=present."},
        "validate": {"type": "boolean", "default": True, "description": "Validate content with visudo before installing."},
    }
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("security.sudo.dropin state must be present or absent")
        if state == "present" and "content" not in params:
            raise PluginValidationError("security.sudo.dropin requires content when state=present")
        name = str(params["name"])
        if "/" in name or name in {".", ".."}:
            raise PluginValidationError("security.sudo.dropin name must be a simple filename")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        dest = f"/etc/sudoers.d/{params['name']}"
        state = str(params.get("state", "present"))
        if state == "absent":
            command = f"if test -e {quote(dest)}; then {sudo_prefix(params, default=True)}rm -f {quote(dest)} && echo {CHANGE_MARKER}; fi"
            rc, out, err = exec_remote(context, command)
            return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.sudo.dropin failed")
        temp_path = upload_text_to_temp(context, str(params["content"]).rstrip() + "\n")
        if bool(params.get("validate", True)):
            rc, out, err = exec_remote(context, f"{sudo_prefix(params, default=True)}visudo -cf {quote(temp_path)}")
            if rc != 0:
                return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.sudo.dropin validation failed")
        rc, out, err = install_uploaded_file(
            context,
            temp_path,
            dest,
            sudo=bool(params.get("sudo", True)),
            mode=str(params.get("mode", "0440")),
            owner="root",
            group="root",
        )
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.sudo.dropin failed", data={"path": dest})

# Extended authorized_keys controls.

def _authorized_key_execute_extended(self: SshAuthorizedKeyPlugin, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
    self.validate(params)
    params = dict(params)
    key = str(params["key"])
    if params.get("fingerprint_assert"):
        rc, out, err = exec_remote(context, f"printf '%s\\n' {quote(key)} | ssh-keygen -lf - | grep -F -- {quote(params['fingerprint_assert'])}")
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="security.ssh.authorized_key.add fingerprint_assert failed")
    if params.get("key_options") and not key.startswith(str(params["key_options"])):
        key = f"{params['key_options']} {key}"
    if params.get("comment_update"):
        parts = key.split()
        if len(parts) >= 2:
            key = " ".join([*parts[:2], str(params["comment_update"])])
    params["key"] = key
    if bool(params.get("exclusive", False)) and str(params.get("state", "present")) == "present":
        user = str(params["user"])
        prefix = sudo_prefix(params, default=True)
        script = r'''
set -eu
user=$1
key=$2
home=$(getent passwd "$user" | cut -d: -f6)
[ -n "$home" ] || { echo "user not found: $user" >&2; exit 1; }
ssh_dir="$home/.ssh"
auth_file="$ssh_dir/authorized_keys"
mkdir -p "$ssh_dir"
printf '%s\n' "$key" > "$auth_file"
chmod 700 "$ssh_dir"
chmod 600 "$auth_file"
chown -R "$user":"$user" "$ssh_dir" 2>/dev/null || true
echo __AUTOMAX_CHANGED__
'''
        rc, out, err = exec_remote(
            context,
            heredoc_to_stdin(
                f"{prefix}sh -s -- {quote(user)} {quote(key)}",
                script,
                prefix="AUTOMAX_SH",
            ),
        )
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="security.ssh.authorized_key.add failed")
    return SshAuthorizedKeyPlugin.execute(self, params, context)


class ExtendedSshAuthorizedKeyPlugin(SshAuthorizedKeyPlugin):
    """security.ssh.authorized_key.add with exclusive, fingerprint and comment controls."""

    optional_params = ("state", "sudo", "key_options", "exclusive", "comment_update", "fingerprint_assert")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return _authorized_key_execute_extended(self, params, context)
