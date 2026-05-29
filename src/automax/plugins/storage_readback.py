# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Storage readback and assertion plugins."""

from __future__ import annotations

import re
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import exec_remote, quote, sudo_prefix


def _lv_size_filter(size: Any) -> str:
    requested = str(size).strip()
    match = re.fullmatch(r"([0-9]+)(?:\.0+)?([kKmMgGtTpPeE])(?:[bB])?", requested)
    if match:
        value, unit = match.groups()
        pattern = rf"^[[:space:]]*{re.escape(value)}(\.0+)?{unit}[[:space:]]*$"
        return f"grep -Ei -- {quote(pattern)}"
    return f"grep -F -- {quote(requested)}"



class LvmFactsPlugin(BasePlugin):
    name = "storage.lvm.facts"
    description = "Collect LVM PV, VG and LV facts from a target."
    optional_params = ("vg", "name", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.lvm.facts is a read-only LVM fact query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        vg_filter = f" {quote(params['vg'])}" if params.get("vg") else ""
        lv_filter = f" {quote('/dev/' + str(params['vg']) + '/' + str(params['name']))}" if params.get("vg") and params.get("name") else ""
        sudo = sudo_prefix(params, default=True)
        return [f"{sudo}pvs --reportformat json; {sudo}vgs --reportformat json{vg_filter}; {sudo}lvs --reportformat json{lv_filter}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.lvm.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"facts": out})


class LvmLvAssertPlugin(BasePlugin):
    name = "storage.lvm.lv.check"
    description = "Assert that an LVM logical volume exists and optionally matches a requested size."
    required_params = ("vg", "name")
    optional_params = ("size", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.lvm.lv.check is a read-only LVM logical-volume assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        lv_path = f"/dev/{params['vg']}/{params['name']}"
        command = f"{sudo_prefix(params, default=True)}lvs --noheadings -o lv_size {quote(lv_path)}"
        if params.get("size"):
            command += f" | {_lv_size_filter(params['size'])}"
        return [command]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.lvm.lv.check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class MountFactsPlugin(BasePlugin):
    name = "storage.mount.facts"
    description = "Collect mounted filesystem facts with findmnt."
    optional_params = ("path", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.mount.facts is a read-only mount fact query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        path = f" {quote(params['path'])}" if params.get("path") else ""
        return [f"findmnt --json{path}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.mount.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"mounts": out})


class FstabValidatePlugin(BasePlugin):
    name = "storage.fstab.validate"
    description = "Validate fstab syntax and optionally dry-run mount resolution."
    optional_params = ("file", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.fstab.validate is a read-only fstab validation"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        file_path = str(params.get("file", "/etc/fstab"))
        return [f"{sudo_prefix(params, default=True)}findmnt --verify --tab-file {quote(file_path)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.fstab.validate failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class SwapStatusPlugin(BasePlugin):
    name = "storage.swap.facts"
    description = "Report active swap files and devices."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.swap.facts is a read-only swap query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return ["swapon --show"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.swap.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"swap": out})


class BlkidAssertPlugin(BasePlugin):
    name = "storage.fs.check"
    description = "Check block-device identity fields reported by blkid."
    required_params = ("device",)
    optional_params = ("fstype", "label", "uuid", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.fs.check is a read-only block-device identity check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        device = quote(params["device"])
        commands = [f"{sudo_prefix(params, default=True)}blkid {device}"]
        if params.get("fstype"):
            commands.append(f"{sudo_prefix(params, default=True)}blkid -o value -s TYPE {device} | grep -Fx -- {quote(params['fstype'])}")
        if params.get("label"):
            commands.append(f"{sudo_prefix(params, default=True)}blkid -o value -s LABEL {device} | grep -Fx -- {quote(params['label'])}")
        if params.get("uuid"):
            commands.append(f"{sudo_prefix(params, default=True)}blkid -o value -s UUID {device} | grep -Fx -- {quote(params['uuid'])}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.fs.check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)


class StorageFsFactsPlugin(BasePlugin):
    name = "storage.fs.facts"
    description = "Collect filesystem identity, mount and usage facts for a device or path."
    optional_params = ("device", "path", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.fs.facts is a read-only filesystem fact query"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=True)
        commands = []
        if params.get("device"):
            commands.append(f"{sudo}blkid {quote(params['device'])} || true")
        if params.get("path"):
            path = quote(params["path"])
            commands.extend([f"findmnt --json {path} || true", f"df -P {path} || true", f"df -Pi {path} || true"])
        if not commands:
            commands.extend([f"{sudo}blkid || true", "findmnt --json", "df -P", "df -Pi"])
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.fs.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"facts": out})


class StorageSwapCheckPlugin(BasePlugin):
    name = "storage.swap.check"
    description = "Check that a swap file or device is active."
    required_params = ("path",)
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.swap.check is a read-only swap assertion"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"swapon --show=NAME --noheadings | grep -Fx -- {quote(params['path'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.swap.check failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err)
