<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Generated plugin reference

This file is generated from the installed plugin metadata.
Do not edit plugin parameter lists here by hand; update plugin metadata and regenerate.

```bash
automax docs generate-plugins --output docs/plugins/generated.md
```

## apparmor

### `apparmor.profile`

Set an AppArmor profile to enforce or complain mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile name or profile file path. |
| `state` | yes | `string` |  | Desired state such as present, absent, started or stopped. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: apparmor.profile
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
  state: enforce
  sudo: true
```

### `apparmor.reload`

Reload one AppArmor profile file or the AppArmor service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | no | `string` |  | AppArmor profile name or profile file path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: apparmor.reload
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
  sudo: true
```

### `apparmor.status`

Read AppArmor status.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.status`: Raw AppArmor status output.

Example:

```yaml
use: apparmor.status
with:
  sudo: true
```

## archive

### `archive.compress`

Compress one remote file to gzip, bzip2 or xz.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `source` | yes | `path` |  | Remote source path to archive. |
| `dest` | yes | `path` |  | Destination path. |
| `compression` | no | `string` | `auto` | Archive compression: auto, none, gzip, bzip2 or xz. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `creates` | no | `path` |  | Remote path that makes the operation idempotent when already present. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: archive.compress
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `archive.decompress`

Decompress one remote gzip, bzip2 or xz file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `path` |  | Remote archive path to extract. |
| `dest` | yes | `path` |  | Destination path. |
| `compression` | no | `string` | `auto` | Archive compression: auto, none, gzip, bzip2 or xz. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `creates` | no | `path` |  | Remote path that makes the operation idempotent when already present. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: archive.decompress
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `archive.tar`

Create a remote tar archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `source` | yes | `path` |  | Remote source path to archive. |
| `dest` | yes | `path` |  | Destination path. |
| `compression` | no | `string` | `auto` | Archive compression: auto, none, gzip, bzip2 or xz. |
| `excludes` | no | `list` |  | Glob patterns excluded from archive creation. |
| `creates` | no | `path` |  | Remote path that makes the operation idempotent when already present. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: archive.tar
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `archive.untar`

Extract a remote tar archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `path` |  | Remote archive path to extract. |
| `dest` | yes | `path` |  | Destination path. |
| `compression` | no | `string` | `auto` | Archive compression: auto, none, gzip, bzip2 or xz. |
| `strip_components` | no | `integer` | `0` | Path components stripped while extracting a tar archive. |
| `creates` | no | `path` |  | Remote path that makes the operation idempotent when already present. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: archive.untar
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `archive.unzip`

Extract a remote zip archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `path` |  | Remote archive path to extract. |
| `dest` | yes | `path` |  | Destination path. |
| `overwrite` | no | `boolean` | `False` | Replace an existing destination when supported. |
| `creates` | no | `path` |  | Remote path that makes the operation idempotent when already present. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: archive.unzip
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `archive.zip`

Create a remote zip archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `source` | yes | `path` |  | Remote source path to archive. |
| `dest` | yes | `path` |  | Destination path. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `excludes` | no | `list` |  | Glob patterns excluded from archive creation. |
| `creates` | no | `path` |  | Remote path that makes the operation idempotent when already present. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: archive.zip
with:
  source: /var/log/app
  dest: /tmp/dest
```

## assert

### `assert.command`

Assert that a remote command matches the requested condition.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `string` |  | Command line to execute. |
| `rc` | no | `integer` | `0` | Expected process return code. |
| `equals` | no | `string` |  | Expected stdout value after trimming whitespace. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |
| `not_contains` | no | `string` |  | Substring that must not appear in stdout. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `get_pty` | no | `boolean` | `False` | Request a pseudo-terminal for the remote command. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: assert.command
with:
  command: echo automax
```

### `assert.disk`

Assert remote disk capacity thresholds.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `min_free_mb` | no | `integer` |  | Minimum free disk space in MiB. |
| `min_free_percent` | no | `number` |  | Minimum free disk percentage. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: assert.disk
with:
  path: /tmp/automax-demo
```

### `assert.file`

Assert that a remote file condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: assert.file
with:
  path: /tmp/automax-demo
```

### `assert.path`

Assert that a remote path condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: assert.path
with:
  path: /tmp/automax-demo
```

### `assert.tcp`

Assert that a TCP host/port is reachable from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `host` | yes | `string` |  | Hostname or IP address to check from the controller. |
| `port` | yes | `integer` |  | TCP port number. |
| `connect_timeout` | no | `number` | `3` | Per-attempt TCP connect timeout in seconds. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.host`: Checked host.
- `data.port`: Checked TCP port.

Example:

```yaml
use: assert.tcp
with:
  host: 127.0.0.1
  port: 22
```

## cron

### `cron.entry`

Manage one /etc/cron.d entry file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `schedule` | yes | `string` |  | Five-field cron schedule. |
| `command` | yes | `string` |  | Command line to execute. |
| `user` | no | `string` | `root` | User field for /etc/cron.d. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `env` | no | `mapping` |  | Environment lines written before the cron entry. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.path`: Installed cron.d file path.

Example:

```yaml
use: cron.entry
with:
  name: myapp-health
  schedule: '*/5 * * * *'
  user: root
  command: /usr/local/bin/myapp-healthcheck
  sudo: true
```

### `cron.file`

Install or remove a complete /etc/cron.d file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `content` | no | `string` |  | Text content to write. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.path`: Installed cron.d file path.

Example:

```yaml
use: cron.file
with:
  name: nginx
```

## db

### `db.mysql.query`

Run MySQL/MariaDB queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `query` | no | `string` |  | SQL query to execute. |
| `statements` | no | `list` |  | SQL statements executed in order inside one transaction. |
| `query_params` | no | `sequence` |  | SQL bind parameters passed to the database driver. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `fetch` | no | `string` | `all` | Database fetch mode: all, one or none. |
| `commit` | no | `boolean` | `True` | Commit the database transaction on success; false rolls it back. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.rows`: Fetched rows for SELECT-style statements.
- `data.scalar`: First column of the first row when output=scalar.
- `data.rowcount`: Driver rowcount when available.

Example:

```yaml
use: db.mysql.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
```

### `db.oracle.query`

Run Oracle queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `query` | no | `string` |  | SQL query to execute. |
| `statements` | no | `list` |  | SQL statements executed in order inside one transaction. |
| `query_params` | no | `sequence` |  | SQL bind parameters passed to the database driver. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `fetch` | no | `string` | `all` | Database fetch mode: all, one or none. |
| `commit` | no | `boolean` | `True` | Commit the database transaction on success; false rolls it back. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.rows`: Fetched rows for SELECT-style statements.
- `data.scalar`: First column of the first row when output=scalar.
- `data.rowcount`: Driver rowcount when available.

Example:

```yaml
use: db.oracle.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
```

### `db.postgres.query`

Run PostgreSQL queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `query` | no | `string` |  | SQL query to execute. |
| `statements` | no | `list` |  | SQL statements executed in order inside one transaction. |
| `query_params` | no | `sequence` |  | SQL bind parameters passed to the database driver. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `fetch` | no | `string` | `all` | Database fetch mode: all, one or none. |
| `commit` | no | `boolean` | `True` | Commit the database transaction on success; false rolls it back. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.rows`: Fetched rows for SELECT-style statements.
- `data.scalar`: First column of the first row when output=scalar.
- `data.rowcount`: Driver rowcount when available.

Example:

```yaml
use: db.postgres.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
```

### `db.sqlite.query`

Run SQLite queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `query` | no | `string` |  | SQL query to execute. |
| `statements` | no | `list` |  | SQL statements executed in order inside one transaction. |
| `query_params` | no | `sequence` |  | SQL bind parameters passed to the database driver. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `fetch` | no | `string` | `all` | Database fetch mode: all, one or none. |
| `commit` | no | `boolean` | `True` | Commit the database transaction on success; false rolls it back. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.rows`: Fetched rows for SELECT-style statements.
- `data.scalar`: First column of the first row when output=scalar.
- `data.rowcount`: Driver rowcount when available.

Example:

```yaml
use: db.sqlite.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
  output: rows
```

## facts

### `facts.gather`

Gather selected remote Linux facts.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `subset` | no | `list` | `['os', 'network']` | Fact subsets: os, network, packages, services. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.os`: Operating system facts.
- `data.network`: Network facts.
- `data.packages`: Package facts.
- `data.services`: Service facts.

Example:

```yaml
use: facts.gather
with:
  subset:
    - os
    - network
    - services
```

### `facts.network`

Gather remote network facts.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.network`: Network facts.

Example:

```yaml
use: facts.network
with:
  sudo: true
```

### `facts.os`

Gather remote operating-system facts.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.os`: Operating system facts.

Example:

```yaml
use: facts.os
with:
  sudo: true
```

### `facts.packages`

Gather remote package facts from dpkg or rpm.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.packages`: Installed package facts.

Example:

```yaml
use: facts.packages
with:
  manager: auto
  sudo: true
```

### `facts.services`

Gather remote systemd service facts.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.services`: systemd service facts.

Example:

```yaml
use: facts.services
with:
  sudo: true
```

## firewalld

### `firewalld.port`

Manage a firewalld port rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `port` | yes | `integer` |  | TCP port number. |
| `protocol` | no | `string` | `tcp` | Network protocol such as tcp or udp. |
| `zone` | no | `string` |  | firewalld zone name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `permanent` | no | `boolean` | `True` | Persist firewalld changes permanently. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: firewalld.port
with:
  port: 443
  protocol: tcp
  zone: public
  state: present
  permanent: true
  reload: true
  sudo: true
```

### `firewalld.reload`

Reload firewalld configuration.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: firewalld.reload
with:
  sudo: true
```

### `firewalld.rich_rule`

Manage a firewalld rich rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `rich_rule` | yes | `string` |  | firewalld rich rule expression. |
| `zone` | no | `string` |  | firewalld zone name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `permanent` | no | `boolean` | `True` | Persist firewalld changes permanently. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: firewalld.rich_rule
with:
  rich_rule: rule family=ipv4 source address=10.0.0.0/8 service name=ssh accept
```

### `firewalld.service`

Manage a firewalld service rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `zone` | no | `string` |  | firewalld zone name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `permanent` | no | `boolean` | `True` | Persist firewalld changes permanently. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: firewalld.service
with:
  service: sshd
```

## fs

### `fs.cd`

Set current remote working directory for the active step.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.cd
with:
  path: /tmp/automax-demo
```

### `fs.chmod`

Set remote file or directory mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `mode` | yes | `string` |  | POSIX file mode, for example 0644 or 0755. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.chmod
with:
  path: /tmp/automax-demo
  mode: 0644
```

### `fs.chown`

Set remote file or directory owner/group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.chown
with:
  path: /tmp/automax-demo
```

### `fs.copy`

Copy a remote file or directory to another remote path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `preserve` | no | `boolean` | `False` | Preserve mode, ownership and timestamps when copying. |
| `overwrite` | no | `boolean` | `False` | Replace an existing destination when supported. |
| `creates` | no | `path` |  | Remote path that makes the operation idempotent when already present. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.copy
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `fs.exists`

Check whether a remote path exists.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.exists`: Boolean path existence result.
- `data.path`: Checked remote path.

Example:

```yaml
use: fs.exists
with:
  path: /tmp/automax-demo
```

### `fs.find`

Find remote paths.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `patterns` | no | `list` |  | Find-name patterns to match. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `max_depth` | no | `integer` |  | Maximum remote find traversal depth. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.find
with:
  path: /tmp/automax-demo
```

### `fs.line`

Ensure an exact line is present or absent in a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `line` | yes | `string` |  | Exact line to ensure in a remote file. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `create` | no | `boolean` | `False` | Create the remote file when ensuring a line is present. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.line
with:
  path: /tmp/automax-demo
  line: KEY=value
```

### `fs.mkdir`

Create a directory with owner/group/mode parameters.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.mkdir
with:
  path: /tmp/automax-demo
```

### `fs.move`

Move or rename a remote path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `overwrite` | no | `boolean` | `False` | Replace an existing destination when supported. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.move
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `fs.read`

Read a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Remote file content.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.path`: Read remote path.

Example:

```yaml
use: fs.read
with:
  path: /tmp/automax-demo
```

### `fs.remove`

Remove a remote file or directory when present.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.remove
with:
  path: /tmp/automax-demo
```

### `fs.replace`

Replace text in a remote file using a regex pattern.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
| `replacement` | yes | `string` |  | Regex replacement text. |
| `count` | no | `integer` | `0` | Maximum regex replacements; 0 means replace all matches. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `backup_path` | no | `path` |  | Explicit backup path for pre-change file content. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.replace
with:
  path: /tmp/automax-demo
  pattern: KEY=.*
  replacement: KEY=new-value
```

### `fs.stat`

Read remote path metadata.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `missing_ok` | no | `boolean` | `False` | Return success with exists=false when the path is missing. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.exists`: Boolean path existence result.
- `data.size`: Path size in bytes.
- `data.mode`: POSIX mode.
- `data.owner`: Owner name.
- `data.group`: Group name.

Example:

```yaml
use: fs.stat
with:
  path: /tmp/automax-demo
```

### `fs.symlink.create`

Create or update a remote symbolic link.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `allow_replace_non_symlink` | no | `boolean` | `False` | Allow force replacement when the destination exists and is not a symlink. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.symlink.create
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `fs.symlink.remove`

Remove a remote symbolic link safely.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.symlink.remove
with:
  path: /tmp/automax-demo
```

### `fs.template`

Render a local Jinja2 template to a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Local Jinja2 template path on the controller. |
| `dest` | yes | `path` |  | Remote destination file path. |
| `mode` | no | `string` |  | Optional remote file mode, for example 0644. |
| `owner` | no | `string` |  | Optional remote file owner. |
| `group` | no | `string` |  | Optional remote file group. |
| `sudo` | no | `boolean` | `False` | Install the rendered file with sudo. |
| `encoding` | no | `string` | `utf-8` | Template and upload encoding. |
| `values` | no | `mapping` |  | Additional values exposed to the template as values.*. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.src`: Rendered template path.
- `data.dest`: Remote destination path

Example:

```yaml
use: fs.template
with:
  src: ./templates/app.conf.j2
  dest: /etc/myapp/app.conf
  mode: '0644'
  sudo: true
```

### `fs.write`

Write text content to a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `content` | yes | `string` |  | Text content to write. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `encoding` | no | `string` | `utf-8` | Text encoding used for command output, HTTP bodies or file content. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.write
with:
  path: /tmp/automax-demo
  content: managed by automax

```

## fstab

### `fstab.entry`

Ensure an /etc/fstab entry is present or absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `fstype` | yes | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
| `opts` | no | `string` | `defaults` | Mount options. |
| `dump` | no | `integer` | `0` | fstab dump field. |
| `passno` | no | `integer` | `0` | fstab fsck pass number. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fstab.entry
with:
  src: /dev/vdb1
  path: /data
  fstype: xfs
  opts: defaults,noatime
  state: present
  sudo: true
```

## group

### `group.create`

Create a remote group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `gid` | no | `integer` |  | Numeric group id. |
| `system` | no | `boolean` | `False` | Create a system user or group. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: group.create
with:
  name: nginx
```

### `group.exists`

Check whether a remote group exists.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.exists`: Whether the remote group exists.
- `data.name`: Checked group name.

Example:

```yaml
use: group.exists
with:
  name: nginx
```

### `group.remove`

Remove a remote group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: group.remove
with:
  name: nginx
```

## http

### `http.assert`

Assert HTTP status and optional body content.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `url` | yes | `string` |  | HTTP URL. |
| `method` | no | `string` | `GET` | HTTP request method. |
| `headers` | no | `mapping` |  | HTTP request headers. |
| `body` | no | `string` |  | Raw HTTP request body. |
| `json` | no | `mapping` |  | JSON HTTP request body. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `encoding` | no | `string` | `utf-8` | Text encoding used for command output, HTTP bodies or file content. |
| `validate_tls` | no | `boolean` | `True` | Validate TLS certificates for HTTPS requests. |
| `expected_status` | no | `integer` | `200` | Expected HTTP status code. |
| `status` | no | `integer` |  | Expected HTTP status code alias. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.status`: HTTP response status code.
- `data.body`: Decoded response body.

Example:

```yaml
use: http.assert
with:
  url: https://example.invalid/health
```

### `http.request`

Perform an HTTP request from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `url` | yes | `string` |  | HTTP URL. |
| `method` | no | `string` | `GET` | HTTP request method. |
| `headers` | no | `mapping` |  | HTTP request headers. |
| `body` | no | `string` |  | Raw HTTP request body. |
| `json` | no | `mapping` |  | JSON HTTP request body. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `encoding` | no | `string` | `utf-8` | Text encoding used for command output, HTTP bodies or file content. |
| `validate_tls` | no | `boolean` | `True` | Validate TLS certificates for HTTPS requests. |
| `expected_status` | no | `integer` | `200` | Expected HTTP status code. |
| `status` | no | `integer` |  | Expected HTTP status code alias. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.status`: HTTP response status code.
- `data.body`: Decoded response body.
- `data.headers`: Response headers.

Example:

```yaml
use: http.request
with:
  url: https://example.invalid/health
```

### `http.wait`

Wait until an HTTP endpoint matches expected status and optional body content.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `url` | yes | `string` |  | HTTP URL. |
| `method` | no | `string` | `GET` | HTTP request method. |
| `headers` | no | `mapping` |  | HTTP request headers. |
| `body` | no | `string` |  | Raw HTTP request body. |
| `json` | no | `mapping` |  | JSON HTTP request body. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `encoding` | no | `string` | `utf-8` | Text encoding used for command output, HTTP bodies or file content. |
| `validate_tls` | no | `boolean` | `True` | Validate TLS certificates for HTTPS requests. |
| `expected_status` | no | `integer` | `200` | Expected HTTP status code. |
| `status` | no | `integer` |  | Expected HTTP status code alias. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.status`: HTTP response status code.
- `data.body`: Decoded response body.

Example:

```yaml
use: http.wait
with:
  url: https://example.invalid/health
```

## kernel

### `kernel.module.load`

Load a Linux kernel module and optionally persist it.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `file` | no | `path` |  | Remote configuration file path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: kernel.module.load
with:
  name: br_netfilter
  persist: true
  sudo: true
```

### `kernel.module.persist`

Persist a Linux kernel module for loading at boot.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `file` | no | `path` |  | Remote configuration file path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: kernel.module.persist
with:
  name: nginx
```

### `kernel.module.unload`

Unload a Linux kernel module and optionally remove persisted entries.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `file` | no | `path` |  | Remote configuration file path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: kernel.module.unload
with:
  name: nginx
```

## local

### `local.command`

Run a local command on the controller host.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `string` |  | Command line to execute. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |
| `env` | no | `mapping` |  | Environment variables for a local command. |
| `shell` | no | `boolean` |  | Run a local command through the platform shell. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `success_rc` | no | `integer` | `0` | Return code considered successful. |
| `changed` | no | `boolean` | `True` | Whether a successful command should be reported as changed. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: local.command
with:
  command: echo automax
  changed: false
```

## mount

### `mount.absent`

Ensure a mount point is unmounted and optionally removed from fstab.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: mount.absent
with:
  path: /tmp/automax-demo
```

### `mount.present`

Ensure a filesystem is mounted and optionally persisted in fstab.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `fstype` | yes | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
| `opts` | no | `string` | `defaults` | Mount options. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `dump` | no | `integer` | `0` | fstab dump field. |
| `passno` | no | `integer` | `0` | fstab fsck pass number. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: mount.present
with:
  src: /dev/vdb1
  path: /data
  fstype: xfs
  opts: defaults,noatime
  persist: true
  sudo: true
```

## nftables

### `nftables.apply`

Validate and apply nftables rules from inline content or a controller file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `content` | no | `string` |  | Text content to write. |
| `src` | no | `path` |  | Source path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: nftables.apply
with:
  src: ./firewall/prod.nft
  sudo: true
```

### `nftables.validate`

Validate nftables rules from inline content or a controller file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `content` | no | `string` |  | Text content to write. |
| `src` | no | `path` |  | Source path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: nftables.validate
with:
  content: managed by automax

  src: /tmp/source
```

## pkg

### `pkg.install`

Install packages on a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.install
with:
  name: nginx
  packages:
    - curl
```

### `pkg.key.add`

Install a package repository signing key for apt or rpm-based systems.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `url` | no | `string` |  | HTTP URL. |
| `content` | no | `string` |  | Text content to write. |
| `src` | no | `path` |  | Source path. |
| `dest` | no | `path` |  | Destination path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.key.add
with:
  name: vendor
  manager: apt
  url: https://repo.example/key.gpg
  sudo: true
```

### `pkg.key.remove`

Remove an apt keyring file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `dest` | no | `path` |  | Destination path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.key.remove
with:
  name: nginx
```

### `pkg.query`

Query package installation state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.query
with:
  name: nginx
  packages:
    - curl
```

### `pkg.remove`

Remove packages from a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.remove
with:
  name: nginx
  packages:
    - curl
```

### `pkg.repo.add`

Install an apt, yum or dnf repository definition.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `repo` | no | `string` |  | Repository definition line or repo file content. |
| `content` | no | `string` |  | Text content to write. |
| `src` | no | `path` |  | Source path. |
| `dest` | no | `path` |  | Destination path. |
| `update_cache` | no | `boolean` | `False` | Refresh package manager metadata after changing repositories. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.repo.add
with:
  name: vendor
  manager: apt
  repo: deb [signed-by=/etc/apt/keyrings/vendor.gpg] https://repo.example stable main
  update_cache: true
  sudo: true
```

### `pkg.repo.remove`

Remove an apt, yum or dnf repository definition.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `dest` | no | `path` |  | Destination path. |
| `update_cache` | no | `boolean` | `False` | Refresh package manager metadata after changing repositories. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.repo.remove
with:
  name: nginx
```

### `pkg.update_cache`

Refresh package manager metadata.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.update_cache
with:
  name: nginx
  packages:
    - curl
```

### `pkg.upgrade`

Upgrade remote packages.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: pkg.upgrade
with:
  name: nginx
  packages:
    - curl
```

## process

### `process.kill`

Kill a remote process by PID or pattern.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pid` | no | `integer` |  | Process id. |
| `pattern` | no | `string` |  | Regex, process pattern or search pattern. |
| `signal` | no | `string` | `TERM` | Signal name or number sent to a process. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `ignore_missing` | no | `boolean` | `True` | Treat missing processes as success. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: process.kill
with:
  pid: 1234
  pattern: KEY=.*
```

### `process.wait`

Wait for a remote process state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pid` | no | `integer` |  | Process id. |
| `pattern` | no | `string` |  | Regex, process pattern or search pattern. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: process.wait
with:
  pid: 1234
  pattern: KEY=.*
```

## remote

### `remote.command`

Run a command on the current remote target via SSH.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `string` |  | Command line to execute. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `pty` | no | `boolean` | `False` | Request a pseudo-terminal for remote.command. |
| `stdin` | no | `string` |  | Text written to remote command standard input. |
| `encoding` | no | `string` | `utf-8` | Text encoding used for command output, HTTP bodies or file content. |
| `success_rc` | no | `integer` | `0` | Return code considered successful. |
| `changed` | no | `boolean` | `True` | Whether a successful command should be reported as changed. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: remote.command
with:
  command: systemctl is-active sshd
  success_rc: 0
```

## selinux

### `selinux.boolean`

Set an SELinux boolean.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `value` | yes | `string` |  | Desired parameter value. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: selinux.boolean
with:
  name: httpd_can_network_connect
  value: true
  persist: true
  sudo: true
```

### `selinux.context`

Manage an SELinux fcontext rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `selinux_type` | yes | `string` |  | SELinux file context type. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: selinux.context
with:
  path: /tmp/automax-demo
  selinux_type: httpd_sys_content_t
```

### `selinux.mode`

Set SELinux runtime and/or persistent mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `state` | yes | `string` |  | Desired state such as present, absent, started or stopped. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: selinux.mode
with:
  state: present
```

### `selinux.restorecon`

Run restorecon on a remote path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: selinux.restorecon
with:
  path: /tmp/automax-demo
```

## ssh

### `ssh.authorized_key`

Ensure an SSH authorized key is present or absent for a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | Remote user account owning authorized_keys. |
| `key` | yes | `string` |  | Authorized key line to manage. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: ssh.authorized_key
with:
  user: deploy
  key: '{{ vars.deploy_public_key }}'
  state: present
  sudo: true
```

## sudoers

### `sudoers.dropin`

Install or remove a sudoers drop-in file with visudo validation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Drop-in filename under /etc/sudoers.d. |
| `content` | no | `string` |  | sudoers content installed when state=present. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `validate` | no | `boolean` | `True` | Validate content with visudo before installing. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.path`: Installed sudoers drop-in path.

Example:

```yaml
use: sudoers.dropin
with:
  name: deploy-myapp
  content: 'deploy ALL=(root) NOPASSWD: /bin/systemctl restart myapp'
  validate: true
  sudo: true
```

## sysctl

### `sysctl.get`

Read a Linux sysctl value.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.name`: sysctl name.
- `data.value`: Current sysctl value.

Example:

```yaml
use: sysctl.get
with:
  name: nginx
```

### `sysctl.persist`

Persist a Linux sysctl value without applying it immediately.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `value` | yes | `string` |  | Desired parameter value. |
| `file` | no | `path` |  | Remote configuration file path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: sysctl.persist
with:
  name: nginx
  value: 1
```

### `sysctl.reload`

Reload Linux sysctl settings from a file or all configured files.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `file` | no | `path` |  | Remote configuration file path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: sysctl.reload
with:
  file: /etc/sysctl.d/99-automax.conf
  sudo: true
```

### `sysctl.set`

Set a Linux sysctl value at runtime and/or persistently.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `value` | yes | `string` |  | Desired parameter value. |
| `runtime` | no | `boolean` | `True` | Apply the change to the running system. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `file` | no | `path` |  | Remote configuration file path. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.name`: sysctl name.
- `data.value`: Desired sysctl value.

Example:

```yaml
use: sysctl.set
with:
  name: net.ipv4.ip_forward
  value: '1'
  runtime: true
  persist: true
  file: /etc/sysctl.d/99-automax.conf
  sudo: true
```

## systemctl

### `systemctl.daemon_reload`

Run systemctl daemon-reload on a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.daemon_reload
with:
  sudo: true
  user: false
```

### `systemctl.disable`

Disable a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.disable
with:
  service: sshd
```

### `systemctl.enable`

Enable a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.enable
with:
  service: sshd
```

### `systemctl.is_active`

Check remote systemd active state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |
| `fail_on_inactive` | no | `boolean` | `False` | Fail when the queried service is not active. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.is_active
with:
  service: sshd
```

### `systemctl.is_enabled`

Check remote systemd enabled state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |
| `fail_on_disabled` | no | `boolean` | `False` | Fail when the queried service is not enabled. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.is_enabled
with:
  service: sshd
```

### `systemctl.mask`

Mask a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.mask
with:
  service: sshd
```

### `systemctl.reload`

Reload a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.reload
with:
  service: sshd
```

### `systemctl.restart`

Restart a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.restart
with:
  service: sshd
```

### `systemctl.start`

Start a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.start
with:
  service: sshd
```

### `systemctl.status`

Read remote systemd service status.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.status
with:
  service: sshd
```

### `systemctl.stop`

Stop a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.stop
with:
  service: sshd
```

### `systemctl.unmask`

Unmask a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | systemd service unit name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: systemctl.unmask
with:
  service: sshd
```

## transfer

### `transfer.download`

Download a remote file or directory to the controller.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.src`: Remote source path.
- `data.dest`: Local destination path.

Example:

```yaml
use: transfer.download
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `transfer.sync`

Sync a local directory tree to a remote directory.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.src`: Local source directory.
- `data.dest`: Remote destination directory.

Example:

```yaml
use: transfer.sync
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `transfer.upload`

Upload a local file or directory to a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.src`: Local source path.
- `data.dest`: Remote destination path

Example:

```yaml
use: transfer.upload
with:
  src: /tmp/source
  dest: /tmp/dest
```

## ufw

### `ufw.disable`

Disable UFW when active.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: ufw.disable
with:
  sudo: true
```

### `ufw.enable`

Enable UFW when inactive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: ufw.enable
with:
  sudo: true
```

### `ufw.rule`

Manage a UFW allow/deny/reject rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `rule` | yes | `string` |  | Firewall action such as allow, deny, reject or limit. |
| `port` | no | `integer` |  | TCP port number. |
| `protocol` | no | `string` | `tcp` | Network protocol such as tcp or udp. |
| `from` | no | `string` |  | Source address for firewall rules. |
| `to` | no | `string` |  | Destination address for firewall rules. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `comment` | no | `string` |  | User account comment or GECOS field. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: ufw.rule
with:
  rule: allow
  port: 22
  protocol: tcp
  from: 10.0.0.0/8
  sudo: true
```

### `ufw.status`

Read UFW status.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.status`: Raw UFW status output.

Example:

```yaml
use: ufw.status
with:
  sudo: true
```

## user

### `user.create`

Create a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `uid` | no | `integer` |  | Numeric user id. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `groups` | no | `list` |  | Supplementary group names. |
| `system` | no | `boolean` | `False` | Create a system user or group. |
| `shell` | no | `boolean` |  | Run a local command through the platform shell. |
| `home` | no | `path` |  | User home directory. |
| `create_home` | no | `boolean` |  | Create the user's home directory when supported by useradd. |
| `comment` | no | `string` |  | User account comment or GECOS field. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: user.create
with:
  name: nginx
```

### `user.exists`

Check whether a remote user exists.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.exists`: Whether the remote user exists.
- `data.name`: Checked username.

Example:

```yaml
use: user.exists
with:
  name: nginx
```

### `user.lock`

Lock a remote user account.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: user.lock
with:
  name: nginx
```

### `user.modify`

Modify a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `uid` | no | `integer` |  | Numeric user id. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `groups` | no | `list` |  | Supplementary group names. |
| `append` | no | `boolean` | `False` | Append supplementary groups instead of replacing the user group list. |
| `shell` | no | `boolean` |  | Run a local command through the platform shell. |
| `home` | no | `path` |  | User home directory. |
| `comment` | no | `string` |  | User account comment or GECOS field. |
| `lock` | no | `boolean` | `False` | Lock the remote user account. |
| `unlock` | no | `boolean` | `False` | Unlock the remote user account. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: user.modify
with:
  name: nginx
```

### `user.remove`

Remove a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `remove_home` | no | `boolean` | `False` | Remove the user's home directory when deleting an account. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: user.remove
with:
  name: nginx
```

### `user.set_password`

Set a remote user's password using a password hash or plaintext value.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `password_hash` | no | `string` |  | crypt(3) password hash passed to usermod --password. |
| `password` | no | `string` |  | Plaintext password; prefer password_hash when possible. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: user.set_password
with:
  name: nginx
```

### `user.unlock`

Unlock a remote user account.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: user.unlock
with:
  name: nginx
```

## wait

### `wait.command`

Wait until a remote command matches the requested condition.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `string` |  | Command line to execute. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `rc` | no | `integer` | `0` | Expected process return code. |
| `equals` | no | `string` |  | Expected stdout value after trimming whitespace. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |
| `not_contains` | no | `string` |  | Substring that must not appear in stdout. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `get_pty` | no | `boolean` | `False` | Request a pseudo-terminal for the remote command. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: wait.command
with:
  command: echo automax
```

### `wait.file`

Wait until a remote file condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: wait.file
with:
  path: /tmp/automax-demo
```

### `wait.path`

Wait until a remote path condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: wait.path
with:
  path: /tmp/automax-demo
```

### `wait.process`

Wait until a remote process condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: wait.process
with:
  pattern: KEY=.*
```

### `wait.tcp`

Wait until a TCP host/port is reachable from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `host` | yes | `string` |  | Hostname or IP address to check from the controller. |
| `port` | yes | `integer` |  | TCP port number. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `connect_timeout` | no | `number` | `3` | Per-attempt TCP connect timeout in seconds. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.host`: Checked host.
- `data.port`: Checked TCP port.

Example:

```yaml
use: wait.tcp
with:
  host: 127.0.0.1
  port: 22
```
