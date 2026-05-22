# Command plugins

Command plugins are the lowest-level execution primitives. Prefer higher-level
macro plugins when they exist because they provide clearer parameters and better
idempotency.

## `local.command`

Runs a command on the controller machine.

```yaml
- id: render_local_report
  use: local.command
  with:
    command: "printf 'run=%s\n' '{{ job.metadata.name }}'"
  register:
    report: stdout.trim
```

Use it for controller-side glue only. Do not use it to hide remote SSH commands.

## `remote.command`

Runs a command on the current target through the step-scoped SSH connection.

```yaml
- id: read_kernel
  use: remote.command
  with:
    command: "uname -r"
  register:
    kernel_version: stdout.trim
```

`remote.command` is intentionally raw. For filesystem, package, service, archive,
transfer, database or HTTP operations, prefer the dedicated plugin names.
