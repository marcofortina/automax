# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote block-device, partition and signature management plugins."""

from __future__ import annotations

from difflib import unified_diff
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, heredoc_to_stdin, quote, result_from_remote, sudo_prefix, sudo_shell_run_function



def _bool(value: Any) -> str:
    return "true" if bool(value) else "false"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise PluginValidationError("value must be a string or list")


class BlockFactsPlugin(BasePlugin):
    """Collect block-device facts from a remote target."""

    name = "storage.block.facts"
    description = "Collect remote block-device facts with lsblk, blkid, udevadm and optional multipath output."
    required_params: tuple[str, ...] = ()
    optional_params = ("devices", "multipath", "udev", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.block.facts is a read-only facts collector and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        devices = _as_list(params.get("devices"))
        device_args = " ".join(quote(item) for item in devices)
        sudo = sudo_prefix(params, default=False)
        commands = [
            f"{sudo}lsblk -J -O {device_args}".rstrip(),
            f"{sudo}blkid {device_args} || true".rstrip(),
        ]
        if bool(params.get("udev", True)):
            for device in devices:
                commands.append(f"udevadm info --query=property --name={quote(device)} || true")
        if bool(params.get("multipath", False)):
            commands.append(f"{sudo}multipath -ll")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.block.facts failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"raw": out})


class BlockIdentityPlugin(BasePlugin):
    """Read stable SCSI identifiers for udev/multipath workflows."""

    name = "storage.block.identity"
    description = "Read a stable block-device identifier with scsi_id and udevadm."
    required_params = ("device",)
    optional_params = ("scsi_id_path", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.block.identity is a read-only identity query and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        scsi_id = str(params.get("scsi_id_path", "/usr/lib/udev/scsi_id"))
        device = quote(params["device"])
        return [
            f"{sudo_prefix(params, default=False)}{quote(scsi_id)} -g -u -d {device}",
            f"udevadm info --query=property --name={device} | egrep '^(ID_SERIAL|ID_SERIAL_SHORT|ID_WWN|DM_UUID)=' || true",
        ]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="storage.block.identity failed")
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data={"device": params["device"], "raw": out})


class BlockRescanPlugin(BasePlugin):
    """Rescan SCSI hosts or one block device."""

    name = "storage.block.scan"
    description = "Rescan remote SCSI hosts or one block device and optionally refresh multipath."
    required_params: tuple[str, ...] = ()
    optional_params = ("device", "udev_settle", "multipath_reload", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.block.scan changes kernel device discovery state and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = sudo_prefix(params, default=False)
        device = params.get("device")
        commands = []
        if device:
            name = str(device).removeprefix("/dev/").split("/", 1)[0]
            commands.append(
                f"test -w /sys/block/{quote(name)}/device/rescan && echo 1 | {sudo}tee /sys/block/{quote(name)}/device/rescan >/dev/null"
            )
        else:
            commands.append(f"for host in /sys/class/scsi_host/host*; do echo '- - -' | {sudo}tee \"$host/scan\" >/dev/null; done")
        if bool(params.get("udev_settle", True)):
            commands.append("udevadm settle")
        if bool(params.get("multipath_reload", False)):
            commands.append(f"{sudo}multipath -r")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.block.scan failed")


class BlockPartitionRescanPlugin(BasePlugin):
    """Ask the kernel to reread one partition table."""

    name = "storage.block.partition.scan"
    description = "Reread one remote partition table with partprobe/blockdev and udev settle."
    required_params = ("device",)
    optional_params = ("udev_settle", "sudo")
    opens_remote_session = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "storage.block.partition.scan asks the kernel to reread partition state and has no file diff preview"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=False)
        device = quote(params["device"])
        commands = [f"{sudo}partprobe {device} || {sudo}blockdev --rereadpt {device}"]
        if bool(params.get("udev_settle", True)):
            commands.append("udevadm settle")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.block.partition.scan failed")


class BlockPartitionPlugin(BasePlugin):
    """Create missing partitions with parted without recreating existing ones."""

    name = "storage.block.partition.apply"
    description = "Conservatively create a partition table and missing partitions with parted."
    required_params = ("device", "label", "partitions")
    optional_params = ("backup", "backup_path", "force", "udev_settle", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        partitions = params.get("partitions")
        if not isinstance(partitions, list) or not partitions:
            raise PluginValidationError("storage.block.partition.apply partitions must be a non-empty list")
        for item in partitions:
            if not isinstance(item, dict):
                raise PluginValidationError("storage.block.partition.apply partition entries must be mappings")
            for key in ("number", "start", "end"):
                if key not in item:
                    raise PluginValidationError(f"storage.block.partition.apply partition missing {key}")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        desired = [f"label: {params['label']}\n"]
        for item in params["partitions"]:
            flags = item.get("flags", []) or []
            if isinstance(flags, str):
                flags = [flags]
            desired.append(
                "partition {number}: {name} {start} {end} flags={flags}\n".format(
                    number=item["number"], name=item.get("name", "primary"), start=item["start"], end=item["end"], flags=",".join(flags) or "-"
                )
            )
        diff = "".join(unified_diff([], desired, fromfile=f"{params['device']} (current)", tofile=f"{params['device']} (desired)"))
        return [{"path": str(params["device"]), "diff": diff, "kind": "partition-plan"}]

    def _script(self) -> str:
        return f'''set -eu
device=$1
label=$2
backup=$3
backup_path=$4
force=$5
udev_settle=$6
use_sudo=$7
shift 7
{sudo_shell_run_function()}
if findmnt -rn --source "$device" >/dev/null 2>&1; then
    echo "refusing to partition mounted device: $device" >&2
    exit 1
fi
if [ "$backup" = "true" ]; then
    if [ -z "$backup_path" ]; then backup_path="/tmp/$(basename "$device").sfdisk.$(date +%Y%m%d%H%M%S).bak"; fi
    run sfdisk --dump "$device" > "$backup_path" || true
fi
current_label=$(parted -m "$device" print 2>/dev/null | awk -F: 'NR==2 {{print $6}}' || true)
partition_count=$(parted -m "$device" print 2>/dev/null | awk -F: 'NR>2 && $1 ~ /^[0-9]+$/ {{count++}} END {{print count+0}}')
if [ "$current_label" != "$label" ]; then
    if [ "$partition_count" -ne 0 ] && [ "$force" != "true" ]; then
        echo "refusing to relabel non-empty device without force: $device" >&2
        exit 1
    fi
    run parted -s "$device" mklabel "$label"
    echo {CHANGE_MARKER}
fi
while [ "$#" -gt 0 ]; do
    number=$1; name=$2; start=$3; end=$4; flags=$5
    shift 5
    if parted -m "$device" print | awk -F: -v n="$number" '$1 == n {{found=1}} END {{exit found ? 0 : 1}}'; then
        continue
    fi
    if [ -n "$name" ]; then
        run parted -s "$device" mkpart "$name" "$start" "$end"
    else
        run parted -s "$device" mkpart primary "$start" "$end"
    fi
    for flag in $flags; do
        run parted -s "$device" set "$number" "$flag" on
    done
    echo {CHANGE_MARKER}
done
run partprobe "$device" || run blockdev --rereadpt "$device"
if [ "$udev_settle" = "true" ]; then udevadm settle; fi
'''

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        args = [
            quote(params["device"]),
            quote(params["label"]),
            quote(_bool(params.get("backup", True))),
            quote(params.get("backup_path", "")),
            quote(_bool(params.get("force", False))),
            quote(_bool(params.get("udev_settle", True))),
            quote(_bool(params.get("sudo", False))),
        ]
        for item in params["partitions"]:
            flags = item.get("flags", []) or []
            if isinstance(flags, str):
                flags = [flags]
            args.extend([quote(item["number"]), quote(item.get("name", "")), quote(item["start"]), quote(item["end"]), quote(" ".join(str(flag) for flag in flags))])
        return [heredoc_to_stdin(f"sh -s -- {' '.join(args)}", self._script(), prefix="AUTOMAX_SH")]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="storage.block.partition.apply failed")


class BlockWipeSignaturesPlugin(BasePlugin):
    """Wipe filesystem signatures only when explicitly forced."""

    name = "storage.block.signatures.wipe"
    description = "Wipe block-device signatures with wipefs after an optional pre-change signature backup."
    required_params = ("device",)
    optional_params = ("backup", "backup_path", "force", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not bool(params.get("force", False)):
            raise PluginValidationError("storage.block.signatures.wipe requires force: true")

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        diff = f"--- {params['device']} (current signatures)\n+++ {params['device']} (desired signatures)\n@@\n-wipefs signatures present if reported by wipefs -n\n+no wipefs signatures\n"
        return [{"path": str(params["device"]), "diff": diff, "kind": "signature-plan"}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=False)
        device = quote(params["device"])
        commands = []
        if bool(params.get("backup", True)):
            backup_path = str(params.get("backup_path") or f"/tmp/{str(params['device']).split('/')[-1]}.wipefs-signatures.bak")
            commands.append(f"{sudo}wipefs -n {device} > {quote(backup_path)}")
        commands.append(f"{sudo}wipefs -a {device}")
        return commands

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, " && ".join(self.manual_commands(params, context)))
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.block.signatures.wipe failed")


class BlockMkfsPlugin(BasePlugin):
    """Create a filesystem on a block device with conservative safeguards."""

    name = "storage.fs.create"
    description = "Create a filesystem on a block device, refusing existing signatures unless force is true."
    required_params = ("device", "fstype")
    optional_params = ("label", "force", "sudo")
    opens_remote_session = True

    def diff_preview(self, params: Dict[str, Any], context: ExecutionContext) -> list[Dict[str, Any]]:
        self.validate(params)
        label = f" label={params['label']}" if params.get("label") else ""
        diff = f"--- {params['device']} (current filesystem)\n+++ {params['device']} (desired filesystem)\n@@\n-current fstype from blkid\n+{params['fstype']}{label}\n"
        return [{"path": str(params["device"]), "diff": diff, "kind": "filesystem-plan"}]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        sudo = sudo_prefix(params, default=False)
        device = quote(params["device"])
        fstype = str(params["fstype"])
        label_arg = f" -L {quote(params['label'])}" if params.get("label") else ""
        force = " -f" if bool(params.get("force", False)) and fstype in {"xfs"} else ""
        guard = "" if bool(params.get("force", False)) else f"test -z \"$({sudo}blkid -o value -s TYPE {device} 2>/dev/null || true)\" && "
        return [f"{guard}{sudo}mkfs.{quote(fstype)}{force}{label_arg} {device}"]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=f"{out}\n{CHANGE_MARKER}\n" if rc == 0 else out, stderr=err, message="storage.fs.create failed")
