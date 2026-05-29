<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Facts gathering

Automax gathers remote Linux facts for conditional workflows, reports and run diagnostics.

```yaml
- id: gather_core_facts
  use: os.facts
  with:
    subset:
      - os
      - network
      - services
  register:
    host_facts: data
```

Individual plugins are also available:

- `os.facts`
- `network.link.facts`
- `os.package.facts`
- `system.service.facts`

Package facts support Debian/Ubuntu through `dpkg-query` and Red Hat-like systems through `rpm`.
