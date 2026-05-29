<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Kernel, mount and storage plugins

## Kernel modules and sysctl

`system.kernel.module.load`, `system.kernel.module.unload` and `system.kernel.module.persist` control
module runtime and boot persistence separately. `system.kernel.sysctl.get`, `system.kernel.sysctl.set`,
`system.kernel.sysctl.persist` and `system.kernel.sysctl.reload` separate runtime reads, runtime writes,
persistent drop-ins and reload operations.

## Block and mount operations

`storage.fs.create` formats a block device, `storage.fs.check` verifies filesystem identity, `storage.fs.facts` collects blkid/findmnt/df readback, and `storage.fs.resize` grows supported filesystems. `storage.block.partition.scan` asks the kernel to re-read partition state after partitioning. Use destructive block operations only with explicit review and backup/restore planning.

`storage.mount.add` and `storage.mount.remove` manage active mounts. `storage.fstab.add` manages
persistent boot-time mount configuration. Keep runtime mount state and `/etc/fstab`
state explicit in jobs so reboot behavior is visible during review.

## Storage readback and assertions

Use `storage.lvm.facts`, `storage.lvm.*.scan`, `storage.lvm.lv.check`, `storage.mount.facts`, `storage.fstab.validate`, `storage.swap.facts`, `storage.swap.check`, `storage.fs.facts`, `storage.fs.check`, `storage.usage.disk.check` and `storage.usage.inode.check` for storage prechecks and postchecks before and after LVM, mount, swap and block-device operations.

## Kernel, sysctl and block safety assertions

Kernel hardening readback/guard plugins include `system.kernel.module.status`,
`system.kernel.module.blacklist`, `system.kernel.boot_param.check` and
`system.kernel.boot_param.remove`. Removing a boot parameter requires `confirm: true`.

Sysctl readback and drop-in management is covered by `system.kernel.sysctl.check`,
`system.kernel.sysctl.facts` and `system.kernel.sysctl.dropin`.

Block-device safety assertions should be placed before destructive storage steps:
`storage.block.size.check`, `storage.fs.check` and `storage.block.empty.check`.
Runtime mount-state assertions belong to `storage.mount.check`, including source-only
or path-specific mounted/unmounted checks.

Mount and fstab helpers are intentionally separate: `storage.mount.*` manages and checks
runtime mount state, while `storage.fstab.*` manages persistent boot-time mount
configuration. Removing fstab entries requires `confirm: true`.

Swap follows the same split: `storage.swap.*` manages and checks runtime swap state,
while persistent boot-time swap configuration belongs in `storage.fstab.*`.

## Quota and usage checks

`storage.quota.set`, `storage.quota.get`, `storage.quota.check` and `storage.quota.facts` cover quota write, point lookup, assertion and mountpoint inventory flows. `storage.usage.disk.check` merges free-space and used-percent checks; `storage.usage.inode.check` covers inode exhaustion gates, including `min_free_inodes`.
