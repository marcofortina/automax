<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Command plugins

Command plugins are the lowest-level execution primitives. Prefer higher-level
macro plugins when they exist because they provide clearer parameters and better
idempotency.

## `command.local.run`

Runs a command on the controller machine.

```yaml
- id: render_local_report
  use: command.local.run
  with:
    command: "printf 'run=%s\n' '{{ job.metadata.name }}'"
  register:
    report: stdout.trim
```

Use it for controller-side glue only. Do not use it to hide remote SSH commands.

## `command.remote.run`

Runs a command on the current target through the step-scoped SSH connection.

```yaml
- id: read_kernel
  use: command.remote.run
  with:
    command: "uname -r"
  register:
    kernel_version: stdout.trim
```

`command.remote.run` is intentionally raw. For filesystem, package, service, archive,
transfer, database or HTTP operations, prefer the dedicated plugin names.


`command.local.run` uses the controller shell for string commands, matching Python `subprocess.run(..., shell=True)`. Keep it for trusted operator-authored jobs and prefer list-style commands in future extensions when shell parsing is not desired.

`command.remote.run` accepts `cwd`, `timeout`, `stdin`, `pty`, `encoding`, `success_rc` and `changed`. Use explicit `cwd` on the substep that needs a working directory instead of relying on implicit shell state.
