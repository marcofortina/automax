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
