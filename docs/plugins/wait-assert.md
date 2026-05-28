<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Wait and assert plugins

`wait.*` plugins poll until a condition becomes true or a timeout expires.
`assert.*` plugins evaluate once and fail immediately if the condition is false.

The public `assert.*` / `wait.*` surface is intentionally shrinking. File,
directory and symlink checks now live in the type-specific filesystem families:
`fs.dir.*`, `fs.file.*` and `fs.symlink.*`.

## `network.connectivity.port_wait` and `network.connectivity.port_check`

Connectivity checks run from the remote target using `nc`.

```yaml
- id: wait_port
  use: network.connectivity.port_wait
  with:
    host: "{{ server.host }}"
    port: 443
    retries: 30
    interval: 2

- id: assert_port
  use: network.connectivity.port_check
  with:
    host: "{{ server.host }}"
    port: 443
```

## Filesystem waits and existence checks

Use the filesystem namespace for remote file, directory and symlink checks.
`*.exists` reports `data.exists`; it fails only when the path exists with the
wrong type. `*.wait` polls with `retries` and `interval`.

```yaml
- id: wait_pid_file
  use: fs.file.wait
  with:
    path: /run/myapp.pid
    state: present
    retries: 6
    interval: 5

- id: check_config_dir
  use: fs.dir.exists
  with:
    path: /etc/myapp
```

## `process.wait`

Waits for a remote process matching a pattern.

```yaml
- id: wait_worker
  use: process.wait
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
