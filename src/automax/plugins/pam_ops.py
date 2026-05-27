# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Explicit PAM hardening and readback plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_file_expr, heredoc_to_stdin, shell_var_ref, tempfile_command, quote, result_from_remote, sudo_prefix



def _diff(path: str, content: str, kind: str) -> list[Dict[str, Any]]:
    return [{"path": path, "kind": kind, "diff": "".join(unified_diff([], content.splitlines(keepends=True), fromfile=f"{path} (current)", tofile=f"{path} (desired)"))}]


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def _service_path(value: Any) -> str:
    raw = str(value)
    if raw.startswith("/"):
        return raw
    if "/" in raw or raw in {".", "..", ""}:
        raise PluginValidationError("PAM service must be a simple service name or an absolute path")
    return f"/etc/pam.d/{raw}"


def _settings_content(settings: Dict[str, Any]) -> str:
    if not isinstance(settings, dict) or not settings:
        raise PluginValidationError("settings must be a non-empty mapping")
    return "".join(f"{key} = {value}\n" for key, value in sorted(settings.items()))


def _backup(path: str, params: Dict[str, Any]) -> str:
    return f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}cp -p {quote(path)} {quote(path + str(params.get('backup_suffix', '.bak')))}"


def _ensure_line(path: str, line: str, params: Dict[str, Any]) -> str:
    return f"grep -Fxq -- {quote(line)} {quote(path)} || printf '%s\\n' {quote(line)} | {sudo_prefix(params, default=True)}tee -a {quote(path)} >/dev/null"


def _service_files(params: Dict[str, Any]) -> list[str]:
    files = _as_list(params.get("service_files"))
    if params.get("service"):
        files.append(_service_path(params["service"]))
    if params.get("services"):
        files.extend(_service_path(item) for item in _as_list(params.get("services")))
    return files


def _state(params: Dict[str, Any]) -> str:
    state = str(params.get("state", "present"))
    if state not in {"present", "absent"}:
        raise PluginValidationError("state must be present or absent")
    return state


def _install_content_command(path: str, content: str, params: Dict[str, Any], mode: str = "0644") -> list[str]:
    tmp_var = "automax_pam_tmp"
    tmp = shell_var_ref(tmp_var)
    commands = [tempfile_command(tmp_var, "pam"), heredoc_to_file_expr(tmp, content)]
    if bool(params.get("backup", True)):
        commands.append(_backup(path, params))
    commands.extend([f"{sudo_prefix(params, default=True)}install -D -m {mode} {tmp} {quote(path)}", f"rm -f {tmp}"])
    return commands


def _settings_file_commands(path: str, settings: Dict[str, Any], params: Dict[str, Any]) -> list[str]:
    commands: list[str] = []
    if bool(params.get("backup", True)):
        commands.append(_backup(path, params))
    commands.append(f"{sudo_prefix(params, default=True)}touch {quote(path)}")
    for key, value in sorted(settings.items()):
        line = f"{key} = {value}"
        commands.append(
            f"if grep -Eq '^[#[:space:]]*{key}[[:space:]]*=' {quote(path)}; then "
            f"{sudo_prefix(params, default=True)}sed -i -E 's|^[#[:space:]]*{key}[[:space:]]*=.*|{line}|' {quote(path)}; "
            f"else printf '%s\\n' {quote(line)} | {sudo_prefix(params, default=True)}tee -a {quote(path)} >/dev/null; fi"
        )
    return commands


class PamServiceLinePlugin(BasePlugin):
    name = "pam.service_line"
    description = "Ensure or remove one exact line in one PAM service file with backup."
    required_params = ("service", "line")
    optional_params = ("state", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        return _service_path(params["service"])

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _state(params)
        if not str(params["line"]).strip():
            raise PluginValidationError("pam.service_line line must not be empty")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = "" if _state(params) == "absent" else str(params["line"]).rstrip() + "\n"
        return _diff(self._path(params), desired, "pam-service-line-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        path = self._path(params)
        line = str(params["line"]).rstrip()
        commands: list[str] = []
        if bool(params.get("backup", True)):
            commands.append(_backup(path, params))
        if _state(params) == "present":
            commands.append(_ensure_line(path, line, params))
        else:
            script = (
                "from pathlib import Path\n"
                f"path = Path({path!r})\n"
                f"line = {line!r}\n"
                "if path.exists():\n"
                "    lines = path.read_text().splitlines()\n"
                "    path.write_text('\\n'.join(item for item in lines if item != line) + ('\\n' if lines else ''))\n"
            )
            commands.append(
                f"test ! -e {quote(path)} || "
                + heredoc_to_stdin(
                    f"{sudo_prefix(params, default=True)}python3 -",
                    script,
                    prefix="AUTOMAX_PY",
                )
            )
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pam.service_line failed")


class PamAccessPlugin(BasePlugin):
    name = "pam.access"
    description = "Manage access.conf entries and optional pam_access service wiring."
    required_params = ("entries",)
    optional_params = ("path", "service", "services", "service_files", "state", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", "/etc/security/access.conf"))

    def _entries(self, params: Dict[str, Any]) -> list[str]:
        raw = params.get("entries")
        if not isinstance(raw, list) or not raw:
            raise PluginValidationError("pam.access entries must be a non-empty list")
        entries: list[str] = []
        for entry in raw:
            if isinstance(entry, dict):
                if {"permission", "users", "origins"}.issubset(entry):
                    entries.append(f"{entry['permission']} : {entry['users']} : {entry['origins']}")
                elif "domain" in entry:
                    entries.append(f"+ : {entry['domain']} : ALL")
                else:
                    raise PluginValidationError("pam.access mapping entries require permission/users/origins")
            else:
                entries.append(str(entry).strip())
        if not all(entries):
            raise PluginValidationError("pam.access entries must not be empty")
        return entries

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        _state(params)
        content = "" if _state(params) == "absent" else "\n".join(self._entries(params)) + "\n"
        previews = _diff(self._path(params), content, "pam-access-plan")
        for path in _service_files(params):
            previews.extend(_diff(path, "account required pam_access.so\n" if _state(params) == "present" else "", "pam-access-service-plan"))
        return previews

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        state = _state(params)
        path = self._path(params)
        entries = self._entries(params)
        commands: list[str] = []
        if bool(params.get("backup", True)):
            commands.append(_backup(path, params))
        commands.append(f"{sudo_prefix(params, default=True)}touch {quote(path)}")
        for line in entries:
            if state == "present":
                commands.append(_ensure_line(path, line, params))
            else:
                commands.append(f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}grep -Fxv -- {quote(line)} {quote(path)} | {sudo_prefix(params, default=True)}tee {quote(path)} >/dev/null")
        service_line = "account required pam_access.so"
        for service_path in _service_files(params):
            if bool(params.get("backup", True)):
                commands.append(_backup(service_path, params))
            commands.append(_ensure_line(service_path, service_line, params) if state == "present" else f"test ! -e {quote(service_path)} || {sudo_prefix(params, default=True)}grep -Fxv -- {quote(service_line)} {quote(service_path)} | {sudo_prefix(params, default=True)}tee {quote(service_path)} >/dev/null")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pam.access failed")


class PamFaillockPlugin(BasePlugin):
    name = "pam.faillock"
    description = "Manage faillock.conf settings and optional pam_faillock service wiring."
    required_params = ("settings",)
    optional_params = ("path", "service", "services", "service_files", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", "/etc/security/faillock.conf"))

    def _service_lines(self) -> list[str]:
        return [
            "auth required pam_faillock.so preauth silent",
            "auth [default=die] pam_faillock.so authfail",
            "account required pam_faillock.so",
        ]

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        content = _settings_content(params["settings"])
        previews = _diff(self._path(params), content, "pam-faillock-plan")
        for path in _service_files(params):
            previews.extend(_diff(path, "\n".join(self._service_lines()) + "\n", "pam-faillock-service-plan"))
        return previews

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        commands = _settings_file_commands(self._path(params), params["settings"], params)
        for path in _service_files(params):
            if bool(params.get("backup", True)):
                commands.append(_backup(path, params))
            for line in self._service_lines():
                commands.append(_ensure_line(path, line, params))
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pam.faillock failed")


class PamPwhistoryPlugin(BasePlugin):
    name = "pam.pwhistory"
    description = "Manage pwhistory.conf settings and optional pam_pwhistory service wiring."
    required_params = ("settings",)
    optional_params = ("path", "service", "services", "service_files", "control", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        return str(params.get("path", "/etc/security/pwhistory.conf"))

    def _line(self, params: Dict[str, Any]) -> str:
        return f"password {params.get('control', 'required')} pam_pwhistory.so use_authtok"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        content = _settings_content(params["settings"])
        previews = _diff(self._path(params), content, "pam-pwhistory-plan")
        for path in _service_files(params):
            previews.extend(_diff(path, self._line(params) + "\n", "pam-pwhistory-service-plan"))
        return previews

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        commands = _settings_file_commands(self._path(params), params["settings"], params)
        line = self._line(params)
        for path in _service_files(params):
            if bool(params.get("backup", True)):
                commands.append(_backup(path, params))
            commands.append(_ensure_line(path, line, params))
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pam.pwhistory failed")


class PamSucceedIfPlugin(BasePlugin):
    name = "pam.succeed_if"
    description = "Ensure or remove one guarded pam_succeed_if condition in a PAM service file."
    required_params = ("service", "condition")
    optional_params = ("type", "control", "state", "backup", "backup_suffix", "sudo")
    opens_remote_session = True

    def _line(self, params: Dict[str, Any]) -> str:
        return f"{params.get('type', 'auth')} {params.get('control', 'requisite')} pam_succeed_if.so {params['condition']}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        state = _state(params)
        return _diff(_service_path(params["service"]), "" if state == "absent" else self._line(params) + "\n", "pam-succeed-if-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        state = _state(params)
        path = _service_path(params["service"])
        line = self._line(params)
        commands: list[str] = []
        if bool(params.get("backup", True)):
            commands.append(_backup(path, params))
        commands.append(_ensure_line(path, line, params) if state == "present" else f"test ! -e {quote(path)} || {sudo_prefix(params, default=True)}grep -Fxv -- {quote(line)} {quote(path)} | {sudo_prefix(params, default=True)}tee {quote(path)} >/dev/null")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)) + f" && echo {CHANGE_MARKER}")
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="pam.succeed_if failed")


class PamValidatePlugin(BasePlugin):
    name = "pam.validate"
    description = "Run read-only sanity checks against explicit PAM service files."
    optional_params = ("service", "services", "service_files", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def _files(self, params: Dict[str, Any]) -> list[str]:
        files = _service_files(params)
        return files or ["/etc/pam.d/login", "/etc/pam.d/sshd", "/etc/pam.d/su"]

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "pam.validate is a read-only PAM service sanity check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        files = " ".join(quote(path) for path in self._files(params))
        awk = "awk 'NF && $1 !~ /^#/ && $1 !~ /^(auth|account|password|session|include|substack|@include)$/ { print FILENAME \":\" FNR \": unsupported PAM control type: \" $0; bad=1 } END { exit bad }'"
        return [f"test -n {quote(files)} && {awk} {files}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pam.validate failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"files": self._files(params)})


class PamStackFactsPlugin(BasePlugin):
    name = "pam.stack_facts"
    description = "Inventory PAM service files and include/substack relationships."
    optional_params = ("service", "services", "service_files", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def _files_expr(self, params: Dict[str, Any]) -> str:
        files = _service_files(params)
        if files:
            return " ".join(quote(path) for path in files)
        return "/etc/pam.d/*"

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "pam.stack_facts is a read-only PAM stack inventory"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        files = self._files_expr(params)
        return [f"for f in {files}; do test -f \"$f\" || continue; echo '###' \"$f\"; grep -En '^[[:space:]]*(auth|account|password|session|include|substack|@include)' \"$f\" || true; done"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pam.stack_facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"pam_stack": out})


class PamAuthselectPlugin(BasePlugin):
    name = "pam.authselect"
    description = "Assert the current authselect profile and enabled features on RHEL-like systems."
    optional_params = ("profile", "features", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def _features(self, params: Dict[str, Any]) -> list[str]:
        return _as_list(params.get("features"))

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "pam.authselect is a read-only authselect profile assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        command = f"{sudo_prefix(params, default=True)}authselect current"
        if params.get("profile"):
            command += f" | grep -F -- {quote(params['profile'])} >/dev/null"
        for feature in self._features(params):
            command += f" && {sudo_prefix(params, default=True)}authselect current | grep -F -- {quote(feature)} >/dev/null"
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="pam.authselect failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"authselect": out})
