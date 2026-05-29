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

`storage.fs.create` formats a block device, `storage.fs.check` verifies filesystem identity, `storage.fs.facts` collects blkid/findmnt/df readback, and `storage.fs.resize` grows supported filesystems. `storage.block.partition.scan` asks the kernel to re-read partition state after partitioning. Use destructive block operations only with explicit review and backup/restore planning.

`storage.mount.add` and `storage.mount.remove` manage active mounts. `storage.fstab.add` manages
persistent boot-time mount configuration. Keep runtime mount state and `/etc/fstab`
state explicit in jobs so reboot behavior is visible during review.

## Storage readback and assertions

Use `storage.lvm.facts`, `storage.lvm.*.scan`, `storage.lvm.lv.check`, `storage.mount.facts`, `storage.fstab.validate`, `storage.swap.facts`, `storage.swap.check`, `storage.fs.facts`, `storage.fs.check`, `storage.usage.disk_check` and `storage.usage.inode_check` for storage prechecks and postchecks before and after LVM, mount, swap and block-device operations.

## Kernel, sysctl and block safety assertions

Kernel hardening readback/guard plugins include `kernel.module.status`,
`kernel.module.blacklist`, `kernel.cmdline_assert` and
`kernel.boot_param_absent`. Removing a boot parameter requires `confirm: true`.

Sysctl readback and drop-in management is covered by `sysctl.assert`,
`sysctl.facts` and `sysctl.dropin`.

Block-device safety assertions should be placed before destructive storage steps:
`storage.block.size_check`, `storage.fs.check`, `storage.block.mount_check`,
`storage.block.empty_check` and `storage.block.not_mounted_check`.

Mount and fstab readback/removal helpers include `storage.mount.check`, `storage.mount.facts`, `storage.fstab.check` and `storage.fstab.remove`. Removing fstab entries requires `confirm: true`.

## Quota and usage checks

`storage.quota.set`, `storage.quota.get`, `storage.quota.check` and `storage.quota.facts` cover quota write, point lookup, assertion and mountpoint inventory flows. `storage.usage.disk_check` merges free-space and used-percent checks; `storage.usage.inode_check` covers inode exhaustion gates.
