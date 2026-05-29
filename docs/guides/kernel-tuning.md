<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Kernel tuning

Automax manages Linux runtime kernel parameters through `system.kernel.sysctl.*` and kernel modules through `system.kernel.module.*`.

```yaml
- id: enable_forwarding
  use: system.kernel.sysctl.set
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
  use: system.kernel.module.load
  with:
    name: br_netfilter
    persist: true
    sudo: true
```

Use `system.kernel.sysctl.get` for checks, `system.kernel.sysctl.reload` to reload persisted files, and `system.kernel.module.unload` / `system.kernel.module.persist` for module lifecycle management.
