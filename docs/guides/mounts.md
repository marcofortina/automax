<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Mount and fstab management

Automax can manage mounted filesystems and `/etc/fstab` entries.

```yaml
- id: mount_data
  use: mount.present
  with:
    src: /dev/vdb1
    path: /data
    fstype: xfs
    opts: defaults,noatime
    persist: true
    sudo: true
```

```yaml
- id: remove_data_mount
  use: mount.absent
  with:
    path: /data
    persist: true
    sudo: true
```

Use `fstab.entry` when you only want to manage persistence without mounting or unmounting immediately.
