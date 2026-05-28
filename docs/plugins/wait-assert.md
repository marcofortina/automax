<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Wait and assert plugins

`wait.*` plugins poll until a condition becomes true or a timeout expires.
`assert.*` plugins evaluate once and fail immediately if the condition is false.

Use `wait.*` after operations that need time to converge. Use `assert.*` as
explicit gates before moving to the next step.

## `wait.tcp` and `assert.tcp`

TCP checks run from the controller.

```yaml
- id: wait_port
  use: wait.tcp
  with:
    host: "{{ server.host }}"
    port: 443
    timeout: 60
    interval: 2

- id: assert_port
  use: assert.tcp
  with:
    host: "{{ server.host }}"
    port: 443
```

## `wait.file`, `wait.path`, `assert.file`, `assert.path`

Remote file/path checks.

```yaml
- id: wait_pid_file
  use: wait.file
  with:
    path: /run/myapp.pid
    state: present
    timeout: 30

- id: assert_config_dir
  use: assert.path
  with:
    path: /etc/myapp
    type: directory
```

`state` can be `present` or `absent`. `type` can be `path`, `file`,
`directory`, `dir` or `symlink`.

## `wait.process`

Waits for a remote process matching a pattern.

```yaml
- id: wait_worker
  use: wait.process
  with:
    pattern: "myapp-worker"
    state: present
    timeout: 60
```

## `assert.disk`

Fails if a remote filesystem has less than the requested free space.

```yaml
- id: assert_free_space
  use: assert.disk
  with:
    path: /var
    min_free_mb: 1024

- id: assert_percent
  use: assert.disk
  with:
    path: /
    min_free_percent: 15
```

Automax intentionally does not provide `check.*` aliases for now. `assert.*`
communicates failure semantics more clearly, while `wait.*` communicates polling.
