<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Mount and fstab management

Automax can manage mounted filesystems and `/etc/fstab` entries.

```yaml
- id: mount_data
  use: storage.mount.add
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
  use: storage.mount.remove
  with:
    path: /data
    persist: true
    sudo: true
```

Use `storage.fstab.add` when you only want to manage persistence without mounting or unmounting immediately.
