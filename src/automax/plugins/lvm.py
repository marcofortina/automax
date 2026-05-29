# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""LVM operation plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_prefix



def _list(value: Any, name: str) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list) or not value:
        raise PluginValidationError(f"{name} must be a non-empty string or list")
    return [str(item) for item in value]


def _plan(path: str, before: str, after: str, kind: str) -> list[Dict[str, Any]]:
    diff = "".join(unified_diff([before + "\n"], [after + "\n"], fromfile=f"{path} (current)", tofile=f"{path} (desired)"))
    return [{"path": path, "diff": diff, "kind": kind}]


class LvmPvPresentPlugin(BasePlugin):
    name = "storage.lvm.pv.add"
    description = "Ensure a block device is initialized as an LVM physical volume."
    required_params = ("device",)
    optional_params = ("force", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(str(params["device"]), "not an LVM PV", "LVM PV present", "lvm-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        force = " -ff -y" if bool(params.get("force", False)) else ""
        device = quote(params["device"])
        return [f"{sudo_prefix(params, default=True)}pvs --noheadings {device} >/dev/null 2>&1 || {sudo_prefix(params, default=True)}pvcreate{force} {device}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.pv.add failed")


class LvmVgPresentPlugin(BasePlugin):
    name = "storage.lvm.vg.add"
    description = "Ensure an LVM volume group exists and contains the requested PV devices."
    required_params = ("name", "devices")
    optional_params = ("force", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(f"vg:{params['name']}", "volume group missing or incomplete", f"volume group {params['name']} with devices {', '.join(_list(params['devices'], 'devices'))}", "lvm-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        name = quote(params["name"])
        devices = _list(params["devices"], "devices")
        quoted = " ".join(quote(item) for item in devices)
        sudo = sudo_prefix(params, default=True)
        create_force = " -f" if bool(params.get("force", False)) else ""
        commands = [f"{sudo}vgs --noheadings {name} >/dev/null 2>&1 || {sudo}vgcreate{create_force} {name} {quoted}"]
        for device in devices:
            quoted_device = quote(device)
            commands.append(
                f"{sudo}pvs --noheadings -o vg_name {quoted_device} 2>/dev/null "
                f"| awk '{{ $1=$1; print }}' | grep -Fx {name} >/dev/null 2>&1 "
                f"|| {sudo}vgextend {name} {quoted_device}"
            )
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.vg.add failed")


class LvmLvPresentPlugin(BasePlugin):
    name = "storage.lvm.lv.add"
    description = "Ensure an LVM logical volume exists, optionally formatting it when newly created."
    required_params = ("vg", "name", "size")
    optional_params = ("fstype", "resizefs", "force", "sudo")
    opens_remote_session = True

    def _lv_path(self, params: Dict[str, Any]) -> str:
        return f"/dev/{params['vg']}/{params['name']}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(self._lv_path(params), "logical volume missing or smaller", f"logical volume present size={params['size']}", "lvm-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        vg = quote(params["vg"])
        name = quote(params["name"])
        size = quote(params["size"])
        lv_path = quote(self._lv_path(params))
        sudo = sudo_prefix(params, default=True)
        create_force = " -y --wipesignatures y" if bool(params.get("force", False)) else ""
        commands = [
            f"{sudo}lvs --noheadings {lv_path} >/dev/null 2>&1 "
            f"|| {sudo}lvcreate{create_force} -n {name} -L {size} {vg}"
        ]
        if params.get("fstype"):
            force = " -f" if bool(params.get("force", False)) else ""
            commands.append(f"{sudo}blkid {lv_path} >/dev/null 2>&1 || {sudo}mkfs.{quote(params['fstype'])}{force} {lv_path}")
        if bool(params.get("resizefs", False)):
            commands.append(f"{sudo}lvextend -r -L {size} {lv_path}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.lv.add failed")


class LvmLvExtendPlugin(BasePlugin):
    name = "storage.lvm.lv.extend"
    description = "Extend an LVM logical volume, optionally resizing the filesystem."
    required_params = ("vg", "name", "size")
    optional_params = ("resizefs", "sudo")
    opens_remote_session = True

    def _lv_path(self, params: Dict[str, Any]) -> str:
        return f"/dev/{params['vg']}/{params['name']}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(self._lv_path(params), "current LV size", f"at least {params['size']}", "lvm-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        resize = " -r" if bool(params.get("resizefs", True)) else ""
        return [f"{sudo_prefix(params, default=True)}lvextend{resize} -L {quote(params['size'])} {quote(self._lv_path(params))}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.lv.extend failed")


class LvmResizeFsPlugin(BasePlugin):
    name = "storage.fs.resize"
    description = "Resize a filesystem after a block or LVM volume change."
    required_params = ("device", "fstype")
    optional_params = ("path", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(str(params.get("path") or params["device"]), "current filesystem size", "filesystem grown to device size", "filesystem-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        fstype = str(params["fstype"])
        device = quote(params["device"])
        sudo = sudo_prefix(params, default=True)
        if fstype in {"xfs"}:
            mountpoint = params.get("path")
            if not mountpoint:
                raise PluginValidationError("storage.fs.resize requires path for xfs")
            return [f"{sudo}xfs_growfs {quote(mountpoint)}"]
        if fstype in {"ext2", "ext3", "ext4"}:
            return [f"{sudo}resize2fs {device}"]
        return [f"{sudo}resizefs {device}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.fs.resize failed")

class LvmSnapshotPlugin(BasePlugin):
    name = "storage.lvm.lv.snapshot"
    description = "Create an idempotent LVM snapshot logical volume."
    required_params = ("vg", "source", "name", "size")
    optional_params = ("sudo",)
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        return f"/dev/{params['vg']}/{params['name']}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(self._path(params), "snapshot missing", f"snapshot of {params['source']} size={params['size']}", "lvm-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}lvs --noheadings {quote(self._path(params))} >/dev/null 2>&1 || {sudo_prefix(params, default=True)}lvcreate -s -n {quote(params['name'])} -L {quote(params['size'])} {quote(params['source'])}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.lv.snapshot failed")


class LvmLvRemovePlugin(BasePlugin):
    name = "storage.lvm.lv.remove"
    description = "Remove an LVM logical volume with an explicit confirm flag."
    required_params = ("path", "confirm")
    optional_params = ("sudo",)
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if params.get("confirm") is not True:
            raise PluginValidationError("storage.lvm.lv.remove requires confirm: true")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        return _plan(str(params["path"]), "logical volume present", "logical volume absent", "lvm-remove-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}lvs --noheadings {quote(params['path'])} >/dev/null 2>&1 && {sudo_prefix(params, default=True)}lvremove -y {quote(params['path'])} || true"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.lv.remove failed")


class LvmVgRemovePlugin(BasePlugin):
    name = "storage.lvm.vg.remove"
    description = "Remove an LVM volume group with an explicit confirm flag."
    required_params = ("name", "confirm")
    optional_params = ("sudo",)
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if params.get("confirm") is not True:
            raise PluginValidationError("storage.lvm.vg.remove requires confirm: true")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _plan(f"vg:{params['name']}", "volume group present", "volume group absent", "lvm-remove-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [f"{sudo_prefix(params, default=True)}vgs --noheadings {quote(params['name'])} >/dev/null 2>&1 && {sudo_prefix(params, default=True)}vgremove -y {quote(params['name'])} || true"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.vg.remove failed")


class LvmPvRemovePlugin(BasePlugin):
    name = "storage.lvm.pv.remove"
    description = "Remove LVM physical-volume metadata with an explicit confirm flag."
    required_params = ("device", "confirm")
    optional_params = ("force", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if params.get("confirm") is not True:
            raise PluginValidationError("storage.lvm.pv.remove requires confirm: true")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _plan(str(params["device"]), "LVM PV metadata present", "LVM PV metadata absent", "lvm-remove-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        force = " -ff" if bool(params.get("force", False)) else ""
        return [f"{sudo_prefix(params, default=True)}pvs --noheadings {quote(params['device'])} >/dev/null 2>&1 && {sudo_prefix(params, default=True)}pvremove{force} -y {quote(params['device'])} || true"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.pv.remove failed")


class LvmThinPoolPlugin(BasePlugin):
    name = "storage.lvm.lv.thin_pool"
    description = "Ensure an LVM thin pool exists."
    required_params = ("vg", "name", "size")
    optional_params = ("metadata_size", "chunksize", "sudo")
    opens_remote_session = True

    def _path(self, params: Dict[str, Any]) -> str:
        return f"/dev/{params['vg']}/{params['name']}"

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        return _plan(self._path(params), "thin pool missing", f"thin pool present size={params['size']}", "lvm-plan")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        args = ["lvcreate", "--type", "thin-pool", "-n", quote(params["name"]), "-L", quote(params["size"])]
        if params.get("metadata_size"):
            args.extend(["--poolmetadatasize", quote(params["metadata_size"])])
        if params.get("chunksize"):
            args.extend(["--chunksize", quote(params["chunksize"])])
        args.append(quote(params["vg"]))
        return [f"{sudo_prefix(params, default=True)}lvs --noheadings {quote(self._path(params))} >/dev/null 2>&1 || {sudo_prefix(params, default=True)}{' '.join(args)}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.lv.thin_pool failed")


class LvmPvScanPlugin(BasePlugin):
    name = "storage.lvm.pv.scan"
    description = "Refresh LVM physical-volume metadata cache."
    required_params: tuple[str, ...] = ()
    optional_params = ("device", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.lvm.pv.scan refreshes runtime LVM metadata and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        device = f" {quote(params['device'])}" if params.get("device") else ""
        return [f"{sudo_prefix(params, default=True)}pvscan --cache{device}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.pv.scan failed")


class LvmVgScanPlugin(BasePlugin):
    name = "storage.lvm.vg.scan"
    description = "Scan LVM volume groups and recreate missing device nodes."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.lvm.vg.scan refreshes runtime LVM metadata and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=True)}vgscan --mknodes"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.vg.scan failed")


class LvmLvScanPlugin(BasePlugin):
    name = "storage.lvm.lv.scan"
    description = "Scan LVM logical volumes."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.lvm.lv.scan refreshes runtime LVM metadata and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return [f"{sudo_prefix(params, default=True)}lvscan"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.lvm.lv.scan failed")
