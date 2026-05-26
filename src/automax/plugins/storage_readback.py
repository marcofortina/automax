# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Storage readback and assertion plugins."""

from __future__ import annotations

import re
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import exec_remote, quote


def _lv_size_filter(size: Any) -> str:
    requested = str(size).strip()
    match = re.fullmatch(r"([0-9]+)(?:\.0+)?([kKmMgGtTpPeE])(?:[bB])?", requested)
    if match:
        value, unit = match.groups()
        pattern = rf"^[[:space:]]*{re.escape(value)}(\.0+)?{unit}[[:space:]]*$"
        return f"grep -Ei -- {quote(pattern)}"
    return f"grep -F -- {quote(requested)}"


def _sudo(params: Dict[str, Any]) -> str:
    return "sudo -n " if bool(params.get("sudo", True)) else ""


class LvmFactsPlugin(BasePlugin):
    name = "lvm.facts"
    description = "Collect LVM PV, VG and LV facts from a target."
    optional_params = ("vg", "name", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "lvm.facts is a read-only LVM fact query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        vg_filter = f" {quote(params['vg'])}" if params.get("vg") else ""
        lv_filter = f" {quote('/dev/' + str(params['vg']) + '/' + str(params['name']))}" if params.get("vg") and params.get("name") else ""
        sudo = _sudo(params)
        return [f"{sudo}pvs --reportformat json; {sudo}vgs --reportformat json{vg_filter}; {sudo}lvs --reportformat json{lv_filter}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="lvm.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"facts": out})


class LvmLvAssertPlugin(BasePlugin):
    name = "lvm.lv_assert"
    description = "Assert that an LVM logical volume exists and optionally matches a requested size."
    required_params = ("vg", "name")
    optional_params = ("size", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "lvm.lv_assert is a read-only LVM logical-volume assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        lv_path = f"/dev/{params['vg']}/{params['name']}"
        command = f"{_sudo(params)}lvs --noheadings -o lv_size {quote(lv_path)}"
        if params.get("size"):
            command += f" | {_lv_size_filter(params['size'])}"
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="lvm.lv_assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class MountFactsPlugin(BasePlugin):
    name = "mount.facts"
    description = "Collect mounted filesystem facts with findmnt."
    optional_params = ("path", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "mount.facts is a read-only mount fact query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        path = f" {quote(params['path'])}" if params.get("path") else ""
        return [f"findmnt --json{path}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="mount.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"mounts": out})


class FstabValidatePlugin(BasePlugin):
    name = "fstab.validate"
    description = "Validate fstab syntax and optionally dry-run mount resolution."
    optional_params = ("file", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "fstab.validate is a read-only fstab validation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        file_path = str(params.get("file", "/etc/fstab"))
        return [f"{_sudo(params)}findmnt --verify --tab-file {quote(file_path)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fstab.validate failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class SwapStatusPlugin(BasePlugin):
    name = "swap.status"
    description = "Report active swap devices and optionally assert one path is active."
    optional_params = ("path", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "swap.status is a read-only swap query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        if params.get("path"):
            return [f"swapon --show=NAME --noheadings | grep -Fx -- {quote(params['path'])}"]
        return ["swapon --show"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="swap.status failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"swap": out})


class BlkidAssertPlugin(BasePlugin):
    name = "blkid.assert"
    description = "Assert block-device identity fields reported by blkid."
    required_params = ("device",)
    optional_params = ("fstype", "label", "uuid", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "blkid.assert is a read-only block-device identity assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        device = quote(params["device"])
        commands = [f"{_sudo(params)}blkid {device}"]
        if params.get("fstype"):
            commands.append(f"{_sudo(params)}blkid -o value -s TYPE {device} | grep -Fx -- {quote(params['fstype'])}")
        if params.get("label"):
            commands.append(f"{_sudo(params)}blkid -o value -s LABEL {device} | grep -Fx -- {quote(params['label'])}")
        if params.get("uuid"):
            commands.append(f"{_sudo(params)}blkid -o value -s UUID {device} | grep -Fx -- {quote(params['uuid'])}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="blkid.assert failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
