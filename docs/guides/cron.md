<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Cron management

Automax manages `/etc/cron.d` entries with explicit files, which keeps changes auditable and easy to remove.

```yaml
- id: install_healthcheck_cron
  use: cron.entry
  with:
    name: myapp-health
    schedule: "*/5 * * * *"
    user: root
    command: /usr/local/bin/myapp-healthcheck
    sudo: true
```

Use `cron.file` when a full cron.d file must be installed verbatim.
