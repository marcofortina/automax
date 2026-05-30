<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Operator diagnostics with `automax doctor`

`automax doctor` checks the local controller environment before you run jobs
against real systems.

```bash
automax doctor
```

Typical output:

```text
Automax doctor
  OK   python: 3.12.3
  OK   automax: 0.1.0
  OK   paramiko: installed
  OK   database.sqlite: installed
  WARN database.postgres: optional driver missing
  WARN database.mysql: optional driver missing
  WARN database.oracle: optional driver missing
  OK   state-dir: /home/operator/automation/.automax/runs
  OK   ssh: /usr/bin/ssh
  OK   plugins: 67 builtin plugins
```

Optional database drivers are reported as warnings because SQLite is builtin and
PostgreSQL, MySQL and Oracle support is installed only when their extras are
needed.

## JSON output

For CI or support scripts:

```bash
automax doctor --json
```

## State directory check

Use `--state-dir` to verify a custom run-state location:

```bash
automax doctor --state-dir /var/lib/automax/runs
```
