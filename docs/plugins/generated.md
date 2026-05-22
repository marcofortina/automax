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

## archive

### `archive.tar`

Create a remote tar archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `source` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `compression` | no | `any` |  | - |
| `excludes` | no | `any` |  | - |
| `creates` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `archive.untar`

Extract a remote tar archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `compression` | no | `any` |  | - |
| `strip_components` | no | `any` |  | - |
| `creates` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `archive.unzip`

Extract a remote zip archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `overwrite` | no | `any` |  | - |
| `creates` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `archive.zip`

Create a remote zip archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `source` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `recursive` | no | `any` |  | - |
| `excludes` | no | `any` |  | - |
| `creates` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

## assert

### `assert.command`

Assert that a remote command matches the requested condition.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `any` |  | - |
| `rc` | no | `any` |  | - |
| `equals` | no | `any` |  | - |
| `contains` | no | `any` |  | - |
| `not_contains` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `get_pty` | no | `any` |  | - |

### `assert.disk`

Assert remote disk capacity thresholds.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `min_free_mb` | no | `any` |  | - |
| `min_free_percent` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `assert.file`

Assert that a remote file condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `state` | no | `any` |  | - |
| `type` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `assert.path`

Assert that a remote path condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `state` | no | `any` |  | - |
| `type` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `assert.tcp`

Assert that a TCP host/port is reachable from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `host` | yes | `any` |  | - |
| `port` | yes | `any` |  | - |
| `connect_timeout` | no | `any` |  | - |

## db

### `db.mysql.query`

Run MySQL/MariaDB queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `any` |  | - |
| `query` | no | `any` |  | - |
| `statements` | no | `any` |  | - |
| `query_params` | no | `any` |  | - |
| `output` | no | `any` |  | - |
| `fetch` | no | `any` |  | - |
| `commit` | no | `any` |  | - |

### `db.oracle.query`

Run Oracle queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `any` |  | - |
| `query` | no | `any` |  | - |
| `statements` | no | `any` |  | - |
| `query_params` | no | `any` |  | - |
| `output` | no | `any` |  | - |
| `fetch` | no | `any` |  | - |
| `commit` | no | `any` |  | - |

### `db.postgres.query`

Run PostgreSQL queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `any` |  | - |
| `query` | no | `any` |  | - |
| `statements` | no | `any` |  | - |
| `query_params` | no | `any` |  | - |
| `output` | no | `any` |  | - |
| `fetch` | no | `any` |  | - |
| `commit` | no | `any` |  | - |

### `db.sqlite.query`

Run SQLite queries or statements from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `any` |  | - |
| `query` | no | `any` |  | - |
| `statements` | no | `any` |  | - |
| `query_params` | no | `any` |  | - |
| `output` | no | `any` |  | - |
| `fetch` | no | `any` |  | - |
| `commit` | no | `any` |  | - |

## fs

### `fs.cd`

Set current remote working directory for the active step.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |

### `fs.chmod`

Set remote file or directory mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `mode` | yes | `any` |  | - |

### `fs.chown`

Set remote file or directory owner/group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |

### `fs.copy`

Copy a remote file or directory to another remote path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `recursive` | no | `any` |  | - |
| `preserve` | no | `any` |  | - |
| `overwrite` | no | `any` |  | - |
| `creates` | no | `any` |  | - |
| `mode` | no | `any` |  | - |
| `owner` | no | `any` |  | - |
| `group` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `fs.exists`

Check whether a remote path exists.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `type` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `fs.find`

Find remote paths.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `patterns` | no | `any` |  | - |
| `type` | no | `any` |  | - |
| `max_depth` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `fs.line`

Ensure an exact line is present or absent in a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `line` | yes | `any` |  | - |
| `state` | no | `any` |  | - |
| `create` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `fs.mkdir`

Create a directory with owner/group/mode parameters.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |

### `fs.move`

Move or rename a remote path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `overwrite` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `fs.read`

Read a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `fs.remove`

Remove a remote file or directory when present.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `recursive` | no | `any` |  | - |
| `force` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `fs.replace`

Replace text in a remote file using a regex pattern.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `pattern` | yes | `any` |  | - |
| `replacement` | yes | `any` |  | - |
| `count` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `fs.stat`

Read remote path metadata.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `missing_ok` | no | `any` |  | - |
| `cwd` | no | `any` |  | - |

### `fs.symlink.create`

Create or update a remote symbolic link.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `force` | no | `any` |  | - |
| `allow_replace_non_symlink` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `fs.symlink.remove`

Remove a remote symbolic link safely.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |

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

- `data.src`: Rendered template path
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
| `path` | yes | `any` |  | - |
| `content` | yes | `any` |  | - |
| `mode` | no | `any` |  | - |
| `owner` | no | `any` |  | - |
| `group` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `encoding` | no | `any` |  | - |

## group

### `group.create`

Create a remote group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `any` |  | - |
| `gid` | no | `any` |  | - |
| `system` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `group.remove`

Remove a remote group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |

## http

### `http.assert`

Assert HTTP status and optional body content.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `url` | yes | `any` |  | - |
| `method` | no | `any` |  | - |
| `headers` | no | `any` |  | - |
| `body` | no | `any` |  | - |
| `json` | no | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `encoding` | no | `any` |  | - |
| `validate_tls` | no | `any` |  | - |
| `expected_status` | no | `any` |  | - |
| `status` | no | `any` |  | - |
| `contains` | no | `any` |  | - |

### `http.request`

Perform an HTTP request from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `url` | yes | `any` |  | - |
| `method` | no | `any` |  | - |
| `headers` | no | `any` |  | - |
| `body` | no | `any` |  | - |
| `json` | no | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `encoding` | no | `any` |  | - |
| `validate_tls` | no | `any` |  | - |
| `expected_status` | no | `any` |  | - |
| `status` | no | `any` |  | - |

### `http.wait`

Wait until an HTTP endpoint matches expected status and optional body content.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `url` | yes | `any` |  | - |
| `method` | no | `any` |  | - |
| `headers` | no | `any` |  | - |
| `body` | no | `any` |  | - |
| `json` | no | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `encoding` | no | `any` |  | - |
| `validate_tls` | no | `any` |  | - |
| `expected_status` | no | `any` |  | - |
| `status` | no | `any` |  | - |
| `contains` | no | `any` |  | - |
| `interval` | no | `any` |  | - |

## local

### `local.command`

Run a local command on the controller host.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `any` |  | - |

## pkg

### `pkg.install`

Install packages on a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `any` |  | - |
| `packages` | no | `any` |  | - |
| `manager` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `pkg.query`

Query package installation state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `any` |  | - |
| `packages` | no | `any` |  | - |
| `manager` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `pkg.remove`

Remove packages from a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `any` |  | - |
| `packages` | no | `any` |  | - |
| `manager` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `pkg.update_cache`

Refresh package manager metadata.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `any` |  | - |
| `packages` | no | `any` |  | - |
| `manager` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `pkg.upgrade`

Upgrade remote packages.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `any` |  | - |
| `packages` | no | `any` |  | - |
| `manager` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

## process

### `process.kill`

Kill a remote process by PID or pattern.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pid` | no | `any` |  | - |
| `pattern` | no | `any` |  | - |
| `signal` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `ignore_missing` | no | `any` |  | - |

### `process.wait`

Wait for a remote process state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pid` | no | `any` |  | - |
| `pattern` | no | `any` |  | - |
| `state` | no | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `interval` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

## remote

### `remote.command`

Run a command on the current remote target via SSH.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `any` |  | - |

## systemctl

### `systemctl.daemon_reload`

Run systemctl daemon-reload on a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.disable`

Disable a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.enable`

Enable a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.is_active`

Check remote systemd active state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |
| `fail_on_inactive` | no | `any` |  | - |

### `systemctl.is_enabled`

Check remote systemd enabled state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |
| `fail_on_disabled` | no | `any` |  | - |

### `systemctl.mask`

Mask a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.reload`

Reload a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.restart`

Restart a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.start`

Start a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.status`

Read remote systemd service status.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.stop`

Stop a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

### `systemctl.unmask`

Unmask a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `user` | no | `any` |  | - |

## transfer

### `transfer.download`

Download a remote file or directory to the controller.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `recursive` | no | `any` |  | - |

### `transfer.sync`

Sync a local directory tree to a remote directory.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |

### `transfer.upload`

Upload a local file or directory to a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `any` |  | - |
| `dest` | yes | `any` |  | - |
| `recursive` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `mode` | no | `any` |  | - |
| `owner` | no | `any` |  | - |
| `group` | no | `any` |  | - |

## user

### `user.create`

Create a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `any` |  | - |
| `uid` | no | `any` |  | - |
| `group` | no | `any` |  | - |
| `groups` | no | `any` |  | - |
| `system` | no | `any` |  | - |
| `shell` | no | `any` |  | - |
| `home` | no | `any` |  | - |
| `create_home` | no | `any` |  | - |
| `comment` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `user.modify`

Modify a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `any` |  | - |
| `uid` | no | `any` |  | - |
| `group` | no | `any` |  | - |
| `groups` | no | `any` |  | - |
| `append` | no | `any` |  | - |
| `shell` | no | `any` |  | - |
| `home` | no | `any` |  | - |
| `comment` | no | `any` |  | - |
| `lock` | no | `any` |  | - |
| `unlock` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `user.remove`

Remove a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `any` |  | - |
| `remove_home` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

## wait

### `wait.command`

Wait until a remote command matches the requested condition.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `interval` | no | `any` |  | - |
| `rc` | no | `any` |  | - |
| `equals` | no | `any` |  | - |
| `contains` | no | `any` |  | - |
| `not_contains` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |
| `get_pty` | no | `any` |  | - |

### `wait.file`

Wait until a remote file condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `state` | no | `any` |  | - |
| `type` | no | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `interval` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `wait.path`

Wait until a remote path condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `any` |  | - |
| `state` | no | `any` |  | - |
| `type` | no | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `interval` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `wait.process`

Wait until a remote process condition is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `any` |  | - |
| `state` | no | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `interval` | no | `any` |  | - |
| `sudo` | no | `any` |  | - |

### `wait.tcp`

Wait until a TCP host/port is reachable from the controller.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `host` | yes | `any` |  | - |
| `port` | yes | `any` |  | - |
| `timeout` | no | `any` |  | - |
| `interval` | no | `any` |  | - |
| `connect_timeout` | no | `any` |  | - |
