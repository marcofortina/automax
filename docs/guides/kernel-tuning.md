<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Kernel tuning

Automax manages Linux runtime kernel parameters through `sysctl.*` and kernel modules through `kernel.module.*`.

```yaml
- id: enable_forwarding
  use: sysctl.set
  with:
    name: net.ipv4.ip_forward
    value: "1"
    runtime: true
    persist: true
    file: /etc/sysctl.d/99-automax.conf
    sudo: true
```

```yaml
- id: load_bridge_filter
  use: kernel.module.load
  with:
    name: br_netfilter
    persist: true
    sudo: true
```

Use `sysctl.get` for checks, `sysctl.reload` to reload persisted files, and `kernel.module.unload` / `kernel.module.persist` for module lifecycle management.
