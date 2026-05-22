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


`local.command` uses the controller shell for string commands, matching Python `subprocess.run(..., shell=True)`. Keep it for trusted operator-authored jobs and prefer list-style commands in future extensions when shell parsing is not desired.

`remote.command` accepts `cwd`, `timeout`, `stdin`, `pty`, `encoding`, `success_rc` and `changed`. `fs.cd` sets step-local `cwd` for later remote plugins without keeping an interactive shell open.
