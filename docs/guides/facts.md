<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Facts gathering

Automax gathers remote Linux facts for conditional workflows, reports and run diagnostics.

```yaml
- id: gather_core_facts
  use: facts.gather
  with:
    subset:
      - os
      - network
      - services
  register:
    host_facts: data
```

Individual plugins are also available:

- `facts.os`
- `facts.network`
- `facts.packages`
- `facts.services`

Package facts support Debian/Ubuntu through `dpkg-query` and Red Hat-like systems through `rpm`.
