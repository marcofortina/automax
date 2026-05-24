<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Kernel, mount and storage plugins

## Kernel modules and sysctl

`kernel.module.load`, `kernel.module.unload` and `kernel.module.persist` control
module runtime and boot persistence separately. `sysctl.get`, `sysctl.set`,
`sysctl.persist` and `sysctl.reload` separate runtime reads, runtime writes,
persistent drop-ins and reload operations.

## Block and mount operations

`block.mkfs` formats a block device. `block.partition_rescan` asks the kernel to
re-read partition state after partitioning. Use destructive block operations only
with explicit review and backup/restore planning.

`mount.present` and `mount.absent` manage active mounts. `fstab.entry` manages
persistent boot-time mount configuration. Keep runtime mount state and `/etc/fstab`
state explicit in jobs so reboot behavior is visible during review.

## Storage readback and assertions

Use `lvm.facts`, `lvm.lv_assert`, `mount.facts`, `fstab.validate`,
`swap.status` and `blkid.assert` for storage prechecks and postchecks before and
after LVM, mount, swap and block-device operations.

## Kernel, sysctl and block safety assertions

Kernel hardening readback/guard plugins include `kernel.module.status`,
`kernel.module.blacklist`, `kernel.cmdline_assert` and
`kernel.boot_param_absent`. Removing a boot parameter requires `confirm: true`.

Sysctl readback and drop-in management is covered by `sysctl.assert`,
`sysctl.facts` and `sysctl.dropin`.

Block-device safety assertions should be placed before destructive storage steps:
`block.size_assert`, `block.fs_assert`, `block.mountpoint_assert`,
`block.empty_assert` and `block.not_mounted_assert`.

Mount and fstab readback/removal helpers include `mount.assert`,
`mount.options_assert`, `fstab.assert` and `fstab.absent`. Removing fstab entries
requires `confirm: true`.
