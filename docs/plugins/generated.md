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

## automax

### `automax.plugin.requirements`

Report remote tools required by one or more plugins without connecting to a target.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `plugin` | no | `string` |  | Plugin name selected for requirements inspection. |
| `plugins` | no | `list` |  | Plugin names selected for requirements inspection. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: automax.plugin.requirements
```

## command

### `command.local.run`

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
use: command.local.run
with:
  command: echo automax
  changed: false
```

### `command.remote.run`

Run a command on the current remote target via SSH.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `command` | yes | `string` |  | Command line to execute. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `pty` | no | `boolean` | `False` | Request a pseudo-terminal for command.remote.run. |
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
use: command.remote.run
with:
  command: systemctl is-active sshd
  success_rc: 0
```

## data

### `data.archive.tar.check`

Assert a remote tar archive is readable and optionally contains entries.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `path` |  | Remote archive path to extract. |
| `compression` | no | `string` | `auto` | Archive compression: auto, none, gzip, bzip2 or xz. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |
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
use: data.archive.tar.check
with:
  archive: /tmp/app.tar.gz
```

### `data.archive.tar.create`

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
use: data.archive.tar.create
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `data.archive.tar.extract`

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
| `safe_extract` | no | `boolean` | `True` | Reject unsafe archive paths before extraction. |
| `checksum_verify` | no | `string` |  | Expected checksum for archive or file verification. |
| `include` | no | `string` |  | PAM include/substack target name. |
| `exclude` | no | `list` |  | Package or archive excludes. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: data.archive.tar.extract
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `data.archive.tar.list`

List files inside a remote tar archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `path` |  | Remote archive path to extract. |
| `compression` | no | `string` | `auto` | Archive compression: auto, none, gzip, bzip2 or xz. |
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
use: data.archive.tar.list
with:
  archive: /tmp/app.tar.gz
```

### `data.archive.zip.check`

Assert a remote zip archive is readable and optionally contains entries.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `path` |  | Remote archive path to extract. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |
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
use: data.archive.zip.check
with:
  archive: /tmp/app.tar.gz
```

### `data.archive.zip.create`

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
use: data.archive.zip.create
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `data.archive.zip.extract`

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
| `safe_extract` | no | `boolean` | `True` | Reject unsafe archive paths before extraction. |
| `checksum_verify` | no | `string` |  | Expected checksum for archive or file verification. |
| `include` | no | `string` |  | PAM include/substack target name. |
| `exclude` | no | `list` |  | Package or archive excludes. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: data.archive.zip.extract
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `data.archive.zip.list`

List files inside a remote zip archive.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `archive` | yes | `path` |  | Remote archive path to extract. |
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
use: data.archive.zip.list
with:
  archive: /tmp/app.tar.gz
```

### `data.backup.directory.create`

Create a compressed tar backup of a remote directory.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `compression` | no | `string` | `auto` | Archive compression: auto, none, gzip, bzip2 or xz. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
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
use: data.backup.directory.create
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `data.backup.file.create`

Create a timestampable backup copy of a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
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
use: data.backup.file.create
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `data.backup.list`

List remote backup artifacts under a directory.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `patterns` | no | `list` |  | Find-name patterns to match. |
| `max_depth` | no | `integer` |  | Maximum remote find traversal depth. |
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
use: data.backup.list
with:
  path: /tmp/automax-demo
```

### `data.backup.manifest.create`

Create or print a deterministic manifest for a backup directory or selected paths.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `root` | yes | `path` |  | Remote root directory for manifest or inventory operations. |
| `dest` | no | `path` |  | Destination path. |
| `paths` | no | `list` |  | Relative paths selected for manifest or inventory operations. |
| `content_checksums` | no | `boolean` | `True` | Include per-file content checksums in generated backup manifests. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
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
use: data.backup.manifest.create
with:
  root: value
```

### `data.backup.prune`

Prune backup artifacts by age and/or retention count.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `patterns` | no | `list` |  | Find-name patterns to match. |
| `older_than_days` | no | `integer` |  | Age threshold in days for pruning old backup artifacts. |
| `keep` | no | `integer` |  | Number of backup artifacts or rotated generations to retain. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: data.backup.prune
with:
  path: /tmp/automax-demo
```

### `data.backup.rotate`

Rotate one backup artifact through numbered generations.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `keep` | yes | `integer` |  | Number of backup artifacts or rotated generations to retain. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: data.backup.rotate
with:
  path: /tmp/automax-demo
  keep: value
```

### `data.backup.verify`

Verify a remote backup artifact checksum without changing state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `checksum_file` | no | `path` |  | Checksum sidecar file path. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
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
use: data.backup.verify
with:
  path: /tmp/automax-demo
```

### `data.compression.bzip2.check`

Assert a remote bzip2 file is readable.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
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
use: data.compression.bzip2.check
with:
  path: /tmp/automax-demo
```

### `data.compression.bzip2.compress`

Compress one remote file with bzip2.

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
use: data.compression.bzip2.compress
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `data.compression.bzip2.decompress`

Decompress one remote bzip2 file.

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
use: data.compression.bzip2.decompress
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `data.compression.gzip.check`

Assert a remote gzip file is readable.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
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
use: data.compression.gzip.check
with:
  path: /tmp/automax-demo
```

### `data.compression.gzip.compress`

Compress one remote file with gzip.

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
use: data.compression.gzip.compress
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `data.compression.gzip.decompress`

Decompress one remote gzip file.

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
use: data.compression.gzip.decompress
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `data.compression.xz.check`

Assert a remote xz file is readable.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
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
use: data.compression.xz.check
with:
  path: /tmp/automax-demo
```

### `data.compression.xz.compress`

Compress one remote file with xz.

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
use: data.compression.xz.compress
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `data.compression.xz.decompress`

Decompress one remote xz file.

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
use: data.compression.xz.decompress
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `data.compression.zstd.check`

Assert a remote zstd file is readable.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
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
use: data.compression.zstd.check
with:
  path: /tmp/automax-demo
```

### `data.compression.zstd.compress`

Compress one remote file with zstd.

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
use: data.compression.zstd.compress
with:
  source: /var/log/app
  dest: /tmp/dest
```

### `data.compression.zstd.decompress`

Decompress one remote zstd file.

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
use: data.compression.zstd.decompress
with:
  archive: /tmp/app.tar.gz
  dest: /tmp/dest
```

### `data.download.url`

Download a URL on the remote target using curl or wget, with optional checksum and backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `url` | yes | `string` |  | HTTP URL. |
| `dest` | yes | `path` |  | Destination path. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
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
use: data.download.url
with:
  url: https://example.invalid/health
  dest: /tmp/dest
```

### `data.restore.apply`

Restore a remote file or tar archive from an explicit backup artifact.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `confirm` | yes | `boolean` |  | Explicit destructive-operation confirmation flag. |
| `archive` | no | `boolean` |  | Treat the source as an archive artifact. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: data.restore.apply
with:
  src: /tmp/source
  dest: /tmp/dest
  confirm: value
```

### `data.restore.preview`

Preview a restore artifact without changing the target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `archive` | no | `boolean` |  | Treat the source as an archive artifact. |
| `checksum_file` | no | `path` |  | Checksum sidecar file path. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
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
use: data.restore.preview
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `data.restore.verify`

Verify that restored content matches a backup artifact.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `archive` | no | `boolean` |  | Treat the source as an archive artifact. |
| `checksum_file` | no | `path` |  | Checksum sidecar file path. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
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
use: data.restore.verify
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `data.transfer.download`

Download a remote file or directory to the controller.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
| `overwrite` | no | `boolean` | `False` | Replace an existing destination when supported. |
| `backup_existing` | no | `boolean` | `False` | Create a backup of an existing destination before replacing it. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `preserve_times` | no | `boolean` | `False` | Preserve source access and modification timestamps when transferring files. |

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
use: data.transfer.download
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `data.transfer.rsync`

Synchronize files with rsync using the current target as the default remote endpoint.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `direction` | no | `string` | `upload` | Transfer direction such as upload, download or local. |
| `archive` | no | `boolean` | `True` | Use rsync archive mode. |
| `compress` | no | `boolean` | `False` | Enable stream compression when supported. |
| `delete` | no | `boolean` | `False` | Delete extraneous destination files when supported. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
| `dry_run` | no | `boolean` | `False` | Render or run without applying changes when supported. |
| `excludes` | no | `list` |  | Glob patterns excluded from archive creation. |
| `ssh_options` | no | `list` |  | Extra ssh options used by rsync. |
| `rsync_path` | no | `path` |  | Remote rsync executable path. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `partial` | no | `boolean` | `False` | Keep partially transferred files. |
| `bwlimit` | no | `integer` |  | Bandwidth limit. |
| `numeric_ids` | no | `boolean` | `False` | Preserve numeric UID/GID values. |
| `itemize_changes` | no | `boolean` | `False` | Show per-file rsync changes. |
| `stats` | no | `boolean` | `False` | Show transfer statistics. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.command`: Executed rsync argument vector.

Example:

```yaml
use: data.transfer.rsync
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `data.transfer.upload`

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
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
| `overwrite` | no | `boolean` | `False` | Replace an existing destination when supported. |
| `backup_existing` | no | `boolean` | `False` | Create a backup of an existing destination before replacing it. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `preserve_times` | no | `boolean` | `False` | Preserve source access and modification timestamps when transferring files. |

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
use: data.transfer.upload
with:
  src: /tmp/source
  dest: /tmp/dest
```

## database

### `database.mysql.check`

Run read-only controller-side MySQL health checks.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `checks` | no | `list` |  | Health checks to run. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `engine` | no | `string` |  | Database engine such as sqlite, postgres, mysql or oracle. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: database.mysql.check
with:
  connection:
    path: /tmp/automax.sqlite
  path: /tmp/automax-demo
```

### `database.mysql.query`

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
use: database.mysql.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
```

### `database.oracle.check`

Run read-only controller-side Oracle health checks.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `checks` | no | `list` |  | Health checks to run. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `engine` | no | `string` |  | Database engine such as sqlite, postgres, mysql or oracle. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: database.oracle.check
with:
  connection:
    path: /tmp/automax.sqlite
  path: /tmp/automax-demo
```

### `database.oracle.query`

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
use: database.oracle.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
```

### `database.postgres.check`

Run read-only controller-side PostgreSQL health checks.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `checks` | no | `list` |  | Health checks to run. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `engine` | no | `string` |  | Database engine such as sqlite, postgres, mysql or oracle. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: database.postgres.check
with:
  connection:
    path: /tmp/automax.sqlite
  path: /tmp/automax-demo
```

### `database.postgres.query`

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
use: database.postgres.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
```

### `database.sqlite.check`

Run read-only controller-side SQLite health checks.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `checks` | no | `list` |  | Health checks to run. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
| `engine` | no | `string` |  | Database engine such as sqlite, postgres, mysql or oracle. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.engine`: Database engine checked.
- `data.checks`: Boolean check results.
- `data.latency_ms`: Measured health-check duration in milliseconds.

Example:

```yaml
use: database.sqlite.check
with:
  connection:
    path: /tmp/automax.sqlite
  path: /tmp/automax-demo
```

### `database.sqlite.query`

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
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `database` | no | `path` |  | SQLite database path or database name, depending on the plugin. |

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
use: database.sqlite.query
with:
  connection:
    path: /tmp/automax.sqlite
  query: SELECT 1 AS value
  output: rows
```

## device

### `device.udev.device.facts`

Read udev properties for a device path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
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
use: device.udev.device.facts
with:
  device: /dev/sdb
```

### `device.udev.device.test`

Run udevadm test for a device sysfs path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
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
use: device.udev.device.test
with:
  device: /dev/sdb
```

### `device.udev.reload`

Reload udev rules.

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
use: device.udev.reload
with:
  sudo: true
```

### `device.udev.rule.check`

Assert that a udev rules file exists and optionally matches rendered content.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `content` | no | `string` |  | Text content to write. |
| `rules` | no | `list` |  | Structured rule entries. |
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
use: device.udev.rule.check
with:
  path: /tmp/automax-demo
```

### `device.udev.rule.remove`

Remove a udev rules file with optional backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: device.udev.rule.remove
with:
  path: /tmp/automax-demo
```

### `device.udev.rule.set`

Install a udev rules file from content or structured rule entries.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `content` | no | `string` |  | Text content to write. |
| `rules` | no | `list` |  | Structured rule entries. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
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
use: device.udev.rule.set
with:
  path: /tmp/automax-demo
```

### `device.udev.rule.validate`

Validate udev rules file syntax with udevadm test where possible.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `file` | yes | `path` |  | Remote configuration file path. |
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
use: device.udev.rule.validate
with:
  file: /etc/sysctl.d/99-automax.conf
```

### `device.udev.settle`

Wait for the udev event queue to settle.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `timeout` | no | `number` |  | Operation timeout in seconds. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: device.udev.settle
with:
  timeout: 60
```

### `device.udev.trigger`

Trigger udev events and optionally wait for settle.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `subsystem` | no | `string` |  | udev subsystem filter. |
| `action` | no | `string` |  | udev action to trigger. |
| `udev_settle` | no | `boolean` | `True` | Wait for udev events to settle after the operation. |
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
use: device.udev.trigger
with:
  subsystem: block
  action: change
```

## fs

### `fs.acl.check`

Check whether POSIX ACL entries are present or absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `acl` | yes | `string` |  | POSIX ACL entry accepted by setfacl. |
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
use: fs.acl.check
with:
  path: /tmp/automax-demo
  acl: value
```

### `fs.acl.get`

Read POSIX ACL entries with getfacl.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: fs.acl.get
with:
  path: /tmp/automax-demo
```

### `fs.acl.restore`

Restore POSIX ACL entries from a getfacl backup file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `file` | yes | `path` |  | Remote configuration file path. |
| `test_only` | no | `boolean` | `False` | Validate without applying when supported. |
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
use: fs.acl.restore
with:
  file: /etc/sysctl.d/99-automax.conf
```

### `fs.acl.set`

Ensure or remove POSIX ACL entries with getfacl backup support.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `acl` | yes | `string` |  | POSIX ACL entry accepted by setfacl. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_path` | no | `path` |  | Explicit backup path for pre-change file content. |
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
use: fs.acl.set
with:
  path: /tmp/automax-demo
  acl: value
```

### `fs.attr.check`

Check whether Linux filesystem attributes are present or absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `attrs` | yes | `string` |  | Linux filesystem attribute flags accepted by chattr. |
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
use: fs.attr.check
with:
  path: /tmp/automax-demo
  attrs: value
```

### `fs.attr.get`

Read Linux filesystem attributes with lsattr.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: fs.attr.get
with:
  path: /tmp/automax-demo
```

### `fs.attr.set`

Set or clear Linux filesystem attributes with chattr.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `attrs` | yes | `string` |  | Linux filesystem attribute flags accepted by chattr. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
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
use: fs.attr.set
with:
  path: /tmp/automax-demo
  attrs: value
```

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

### `fs.dir.check`

Check whether a real directory exists, failing if another path type exists there.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.exists`: Boolean directory existence result.
- `data.path`: Checked remote path.
- `data.type`: Expected filesystem type.

Example:

```yaml
use: fs.dir.check
with:
  path: /tmp/automax-demo
```

### `fs.dir.create`

Create a real directory, refusing files and symlinks at the destination.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
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
use: fs.dir.create
with:
  path: /tmp/automax-demo
```

### `fs.dir.remove`

Remove a real directory, refusing files and symlinks. Non-empty directories require recursive=true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
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
use: fs.dir.remove
with:
  path: /tmp/automax-demo
```

### `fs.dir.wait`

Wait for a real directory to become present or absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `retries` | no | `integer` | `12` | Maximum polling attempts before a wait operation fails. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.state`: Desired directory state.
- `data.attempts`: Polling attempts used.

Example:

```yaml
use: fs.dir.wait
with:
  path: /tmp/automax-demo
```

### `fs.file.check`

Check whether a real regular file exists, failing if another path type exists there.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.exists`: Boolean regular-file existence result.
- `data.path`: Checked remote path.
- `data.type`: Expected filesystem type.

Example:

```yaml
use: fs.file.check
with:
  path: /tmp/automax-demo
```

### `fs.file.create`

Create a real regular file, refusing directories and symlinks at the destination.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
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
use: fs.file.create
with:
  path: /tmp/automax-demo
```

### `fs.file.line`

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
| `backup_before` | no | `boolean` | `False` | Capture or copy the current state before applying a potentially destructive change. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `validate_command` | no | `string` |  | Command used to validate generated file content. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.file.line
with:
  path: /tmp/automax-demo
  line: KEY=value
```

### `fs.file.read`

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
use: fs.file.read
with:
  path: /tmp/automax-demo
```

### `fs.file.remove`

Remove a real regular file, refusing directories and symlinks.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
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
use: fs.file.remove
with:
  path: /tmp/automax-demo
```

### `fs.file.replace`

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
| `backup_before` | no | `boolean` | `False` | Capture or copy the current state before applying a potentially destructive change. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `backup_path` | no | `path` |  | Explicit backup path for pre-change file content. |
| `validate_command` | no | `string` |  | Command used to validate generated file content. |
| `match_count_assert` | no | `integer` |  | Expected number of regex matches. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.file.replace
with:
  path: /tmp/automax-demo
  pattern: KEY=.*
  replacement: KEY=new-value
```

### `fs.file.template`

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
| `backup_before` | no | `boolean` | `False` | Capture or copy the current state before applying a potentially destructive change. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `validate_command` | no | `string` |  | Command used to validate generated file content. |
| `sensitive` | no | `boolean` | `False` | Mask sensitive content in previews or logs. |
| `atomic` | no | `boolean` | `True` | Install generated file content via a temporary path and final rename where possible. |

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
use: fs.file.template
with:
  src: ./templates/app.conf.j2
  dest: /etc/myapp/app.conf
  mode: '0644'
  sudo: true
```

### `fs.file.wait`

Wait for a real regular file to become present or absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `retries` | no | `integer` | `12` | Maximum polling attempts before a wait operation fails. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.state`: Desired regular-file state.
- `data.attempts`: Polling attempts used.

Example:

```yaml
use: fs.file.wait
with:
  path: /tmp/automax-demo
```

### `fs.file.write`

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
| `backup_before` | no | `boolean` | `False` | Capture or copy the current state before applying a potentially destructive change. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `validate_command` | no | `string` |  | Command used to validate generated file content. |
| `sensitive` | no | `boolean` | `False` | Mask sensitive content in previews or logs. |
| `atomic` | no | `boolean` | `True` | Install generated file content via a temporary path and final rename where possible. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.file.write
with:
  path: /tmp/automax-demo
  content: managed by automax

```

### `fs.object.copy`

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
use: fs.object.copy
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `fs.object.find`

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
use: fs.object.find
with:
  path: /tmp/automax-demo
```

### `fs.object.move`

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
use: fs.object.move
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `fs.object.stat`

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
use: fs.object.stat
with:
  path: /tmp/automax-demo
```

### `fs.permission.mode`

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
use: fs.permission.mode
with:
  path: /tmp/automax-demo
  mode: 0644
```

### `fs.permission.owner`

Set remote file or directory owner/group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `recursive` | no | `boolean` | `False` | Recurse into directories. |
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
use: fs.permission.owner
with:
  path: /tmp/automax-demo
```

### `fs.symlink.check`

Check whether a symbolic link exists, failing if another path type exists there.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.exists`: Boolean symlink existence result.
- `data.path`: Checked remote path.
- `data.type`: Expected filesystem type.

Example:

```yaml
use: fs.symlink.check
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

### `fs.symlink.wait`

Wait for a symbolic link to become present or absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `retries` | no | `integer` | `12` | Maximum polling attempts before a wait operation fails. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `cwd` | no | `path` |  | Remote or local working directory for this operation. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.state`: Desired symlink state.
- `data.attempts`: Polling attempts used.

Example:

```yaml
use: fs.symlink.wait
with:
  path: /tmp/automax-demo
```

## identity

### `identity.group.check`

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
use: identity.group.check
with:
  name: nginx
```

### `identity.group.create`

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
use: identity.group.create
with:
  name: nginx
```

### `identity.group.member.remove`

Remove a user from a group after explicit confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
| `group` | yes | `string` |  | Group name. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: identity.group.member.remove
with:
  user: deploy
  group: app
```

### `identity.group.members`

List members of a group.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `group` | yes | `string` |  | Group name. |
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
use: identity.group.members
with:
  group: app
```

### `identity.group.remove`

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
use: identity.group.remove
with:
  name: nginx
```

### `identity.user.check`

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
use: identity.user.check
with:
  name: nginx
```

### `identity.user.create`

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
use: identity.user.create
with:
  name: nginx
```

### `identity.user.facts`

Read passwd, shadow lock and group facts for a user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
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
use: identity.user.facts
with:
  user: deploy
```

### `identity.user.groups_check`

Assert required group membership for a user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
| `groups` | yes | `list` |  | Supplementary group names. |
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
use: identity.user.groups_check
with:
  user: deploy
  groups:
    - app
```

### `identity.user.home_check`

Assert a user's home directory path, owner or mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
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
use: identity.user.home_check
with:
  user: deploy
```

### `identity.user.lock`

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
use: identity.user.lock
with:
  name: nginx
```

### `identity.user.modify`

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
use: identity.user.modify
with:
  name: nginx
```

### `identity.user.remove`

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
use: identity.user.remove
with:
  name: nginx
```

### `identity.user.set_password`

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
use: identity.user.set_password
with:
  name: nginx
```

### `identity.user.shell_check`

Assert a user's login shell.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
| `shell` | yes | `string` |  | Expected login shell. |
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
use: identity.user.shell_check
with:
  user: deploy
  shell: /bin/bash
```

### `identity.user.unlock`

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
use: identity.user.unlock
with:
  name: nginx
```

## network

### `network.connectivity.port_check`

Check TCP or UDP connectivity from the remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `host` | yes | `string` |  | Hostname or IP address to check from the controller. |
| `port` | yes | `integer` |  | TCP port number. |
| `protocol` | no | `string` | `tcp` | Network protocol such as tcp or udp. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

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
use: network.connectivity.port_check
with:
  host: 127.0.0.1
  port: 22
```

### `network.connectivity.port_wait`

Wait for TCP or UDP connectivity from the remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `host` | yes | `string` |  | Hostname or IP address to check from the controller. |
| `port` | yes | `integer` |  | TCP port number. |
| `protocol` | no | `string` | `tcp` | Network protocol such as tcp or udp. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `interval` | no | `number` | `2` | Polling interval in seconds. |
| `retries` | no | `integer` | `12` | Maximum polling attempts before a wait operation fails. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

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
use: network.connectivity.port_wait
with:
  host: 127.0.0.1
  port: 22
```

### `network.dns.check`

Assert resolver nameserver, search and option entries from /etc/resolv.conf.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `nameservers` | no | `list` |  | Resolver nameserver addresses. |
| `search` | no | `list` |  | Resolver search domains. |
| `options` | no | `list` |  | Resolver options. |
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
use: network.dns.check
with:
  nameservers:
    - 192.0.2.53
  search:
    - example.com
```

### `network.dns.config`

Configure DNS resolver settings using the backend-aware resolver implementation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `backend` | no | `string` |  | Operation backend such as auto, runtime, networkmanager, systemd-networkd, ifcfg, plain-file, systemd-resolved or resolvconf. |
| `nameservers` | no | `list` |  | Resolver nameserver addresses. |
| `search` | no | `list` |  | Resolver search domains. |
| `options` | no | `list` |  | Resolver options. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `nm_connection` | no | `string` |  | NetworkManager connection profile used for persistent DNS changes. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: network.dns.config
with:
  backend: auto
  nameservers:
    - 192.0.2.53
```

### `network.dns.facts`

Detect the active DNS resolver backend without changing resolver configuration.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: network.dns.facts
with:
  sudo: true
```

### `network.firewall.firewalld.forward_port`

Manage firewalld forward-port rules.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `port` | yes | `integer` |  | TCP port number. |
| `to_port` | yes | `integer` |  | Forward destination port. |
| `protocol` | no | `string` | `tcp` | Network protocol such as tcp or udp. |
| `to_addr` | no | `string` |  | Forward destination address. |
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
use: network.firewall.firewalld.forward_port
with:
  port: 22
  to_port: value
```

### `network.firewall.firewalld.icmp_block`

Manage a firewalld ICMP block.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `icmp_type` | yes | `string` |  | firewalld ICMP type name. |
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
use: network.firewall.firewalld.icmp_block
with:
  icmp_type: value
```

### `network.firewall.firewalld.list`

List firewalld rules for one zone or all zones.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `zone` | no | `string` |  | firewalld zone name. |
| `permanent` | no | `boolean` | `True` | Persist firewalld changes permanently. |
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
use: network.firewall.firewalld.list
with:
  zone: public
  permanent: true
```

### `network.firewall.firewalld.masquerade`

Manage firewalld masquerading for a zone.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
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
use: network.firewall.firewalld.masquerade
with:
  zone: public
  state: present
```

### `network.firewall.firewalld.port`

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
| `runtime` | no | `boolean` | `True` | Apply the change to the running system. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `reload_mode` | no | `string` | `none` | Firewall reload behavior: none, reload or complete-reload. |
| `query_only` | no | `boolean` | `False` | Query rule state without changing it. |
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
use: network.firewall.firewalld.port
with:
  port: 443
  protocol: tcp
  zone: public
  state: present
  permanent: true
  reload: true
  sudo: true
```

### `network.firewall.firewalld.reload`

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
use: network.firewall.firewalld.reload
with:
  sudo: true
```

### `network.firewall.firewalld.rich_rule`

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
| `runtime` | no | `boolean` | `True` | Apply the change to the running system. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `reload_mode` | no | `string` | `none` | Firewall reload behavior: none, reload or complete-reload. |
| `query_only` | no | `boolean` | `False` | Query rule state without changing it. |
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
use: network.firewall.firewalld.rich_rule
with:
  rich_rule: rule family=ipv4 source address=10.0.0.0/8 service name=ssh accept
```

### `network.firewall.firewalld.service`

Manage a firewalld service rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `zone` | no | `string` |  | firewalld zone name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `permanent` | no | `boolean` | `True` | Persist firewalld changes permanently. |
| `runtime` | no | `boolean` | `True` | Apply the change to the running system. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `reload_mode` | no | `string` | `none` | Firewall reload behavior: none, reload or complete-reload. |
| `query_only` | no | `boolean` | `False` | Query rule state without changing it. |
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
use: network.firewall.firewalld.service
with:
  service: sshd
```

### `network.firewall.firewalld.source`

Manage a firewalld source in a zone.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `source` | yes | `string` |  | firewalld source address, network or ipset. |
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
use: network.firewall.firewalld.source
with:
  source: 10.0.0.0/8
  zone: public
  state: present
  sudo: true
```

### `network.firewall.firewalld.status`

Read firewalld daemon state, default zone and active zones.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: network.firewall.firewalld.status
with:
  sudo: true
```

### `network.firewall.firewalld.zone`

Read one firewalld zone configuration.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `zone` | yes | `string` |  | firewalld zone name. |
| `permanent` | no | `boolean` | `True` | Persist firewalld changes permanently. |
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
use: network.firewall.firewalld.zone
with:
  zone: public
```

### `network.firewall.iptables.chain`

Read one iptables or ip6tables chain.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `chain` | yes | `string` |  | Firewall chain name. |
| `table` | no | `string` |  | Routing table name or number. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
| `numeric` | no | `boolean` | `True` | Use numeric address and service output when supported. |
| `verbose` | no | `boolean` | `False` | Include verbose firewall listing output when supported. |
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
use: network.firewall.iptables.chain
with:
  chain: value
```

### `network.firewall.iptables.counter_check`

Assert iptables chain packet counters are above a threshold.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `chain` | yes | `string` |  | Firewall chain name. |
| `table` | no | `string` |  | Routing table name or number. |
| `min_packets` | no | `integer` | `1` | Minimum firewall counter packet threshold. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
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
use: network.firewall.iptables.counter_check
with:
  chain: value
```

### `network.firewall.iptables.delete`

Delete an iptables rule after explicit confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `chain` | yes | `string` |  | Firewall chain name. |
| `rule` | yes | `string` |  | Firewall action such as allow, deny, reject or limit. |
| `table` | no | `string` |  | Routing table name or number. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: network.firewall.iptables.delete
with:
  chain: value
  rule: allow
```

### `network.firewall.iptables.list`

List iptables or ip6tables rules for a table or chain.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `table` | no | `string` |  | Routing table name or number. |
| `chain` | no | `string` |  | Firewall chain name. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
| `numeric` | no | `boolean` | `True` | Use numeric address and service output when supported. |
| `verbose` | no | `boolean` | `False` | Include verbose firewall listing output when supported. |
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
use: network.firewall.iptables.list
with:
  table: main
```

### `network.firewall.iptables.policy`

Read or set an iptables built-in chain default policy.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `chain` | yes | `string` |  | Firewall chain name. |
| `table` | no | `string` |  | Routing table name or number. |
| `policy` | no | `string` |  | Default firewall policy such as ACCEPT or DROP. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
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
use: network.firewall.iptables.policy
with:
  chain: value
```

### `network.firewall.iptables.restore`

Restore iptables or ip6tables rules from a ruleset file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
| `test_only` | no | `boolean` | `False` | Validate without applying when supported. |
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
use: network.firewall.iptables.restore
with:
  src: /tmp/source
```

### `network.firewall.iptables.rule`

Ensure an iptables rule is present or absent in a table and chain.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `chain` | yes | `string` |  | Firewall chain name. |
| `rule` | yes | `string` |  | Firewall action such as allow, deny, reject or limit. |
| `table` | no | `string` |  | Routing table name or number. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
| `position` | no | `integer` |  | Insertion position for ordered firewall rule backends. |
| `comment` | no | `string` |  | User account comment or GECOS field. |
| `wait` | no | `integer` |  | iptables -w lock wait timeout in seconds. |
| `save_after` | no | `boolean` | `False` | Persist runtime firewall state after changing a rule. |
| `dest` | no | `path` |  | Destination path. |
| `backup_before` | no | `boolean` | `False` | Capture or copy the current state before applying a potentially destructive change. |
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
use: network.firewall.iptables.rule
with:
  chain: value
  rule: allow
```

### `network.firewall.iptables.rule_check`

Assert an iptables rule exists.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `chain` | yes | `string` |  | Firewall chain name. |
| `rule` | yes | `string` |  | Firewall action such as allow, deny, reject or limit. |
| `table` | no | `string` |  | Routing table name or number. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
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
use: network.firewall.iptables.rule_check
with:
  chain: value
  rule: allow
```

### `network.firewall.iptables.save`

Save current iptables or ip6tables rules to a persistent file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `dest` | yes | `path` |  | Destination path. |
| `ipv6` | no | `boolean` | `False` | Use IPv6 command variant when supported. |
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
use: network.firewall.iptables.save
with:
  dest: /tmp/dest
```

### `network.firewall.nftables.apply`

Validate and apply nftables rules from inline content or a controller file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `content` | no | `string` |  | Text content to write. |
| `src` | no | `path` |  | Source path. |
| `backup_before` | no | `boolean` | `False` | Capture or copy the current state before applying a potentially destructive change. |
| `persistent_file` | no | `path` |  | Persistent firewall configuration file to install after validation. |
| `reload_service` | no | `string` |  | Service name to reload after installing persistent firewall configuration. |
| `check_only` | no | `boolean` | `False` | Validate the requested change without applying it. |
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
use: network.firewall.nftables.apply
with:
  src: ./firewall/prod.nft
  sudo: true
```

### `network.firewall.nftables.export`

Export the active nftables ruleset to stdout or a remote file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `family` | no | `string` | `inet` | nftables address family such as ip, ip6, inet, arp, bridge or netdev. |
| `table` | no | `string` |  | Routing table name or number. |
| `handle` | no | `boolean` | `False` | Include nftables rule handles when listing rules. |
| `dest` | no | `path` |  | Destination path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: network.firewall.nftables.export
with:
  family: inet
  table: main
```

### `network.firewall.nftables.list`

List the active nftables ruleset or one table.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `family` | no | `string` | `inet` | nftables address family such as ip, ip6, inet, arp, bridge or netdev. |
| `table` | no | `string` |  | Routing table name or number. |
| `handle` | no | `boolean` | `False` | Include nftables rule handles when listing rules. |
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
use: network.firewall.nftables.list
with:
  family: inet
  table: main
```

### `network.firewall.nftables.rollback_file`

Apply an nftables rollback ruleset file after explicit confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `file` | yes | `path` |  | Remote configuration file path. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: network.firewall.nftables.rollback_file
with:
  file: /etc/sysctl.d/99-automax.conf
```

### `network.firewall.nftables.ruleset_check`

Assert the active nftables ruleset contains a fragment.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `fragment` | yes | `string` |  | Expected configuration or ruleset fragment. |
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
use: network.firewall.nftables.ruleset_check
with:
  fragment: value
```

### `network.firewall.nftables.validate`

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
use: network.firewall.nftables.validate
with:
  content: managed by automax

  src: /tmp/source
```

### `network.firewall.ufw.delete`

Delete a UFW rule after explicit confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `rule` | yes | `string` |  | Firewall action such as allow, deny, reject or limit. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: network.firewall.ufw.delete
with:
  rule: allow
```

### `network.firewall.ufw.disable`

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
use: network.firewall.ufw.disable
with:
  sudo: true
```

### `network.firewall.ufw.enable`

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
use: network.firewall.ufw.enable
with:
  sudo: true
```

### `network.firewall.ufw.reset`

Reset UFW after explicit confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: network.firewall.ufw.reset
with:
  sudo: true
```

### `network.firewall.ufw.rule`

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
use: network.firewall.ufw.rule
with:
  rule: allow
  port: 22
  protocol: tcp
  from: 10.0.0.0/8
  sudo: true
```

### `network.firewall.ufw.status`

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
use: network.firewall.ufw.status
with:
  sudo: true
```

### `network.http.check`

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
use: network.http.check
with:
  url: https://example.invalid/health
```

### `network.http.request`

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
use: network.http.request
with:
  url: https://example.invalid/health
```

### `network.http.wait`

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
use: network.http.wait
with:
  url: https://example.invalid/health
```

### `network.link.bond`

Create or update a runtime and optional persistent Linux bonding interface.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `interfaces` | yes | `list` |  | Network interfaces to include in a bond or aggregate. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `miimon` | no | `integer` | `100` | Bond link monitoring interval in milliseconds. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `backend` | no | `string` |  | Operation backend such as auto, runtime, networkmanager, systemd-networkd, ifcfg, plain-file, systemd-resolved or resolvconf. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: network.link.bond
with:
  name: nginx
  interfaces:
    - eth1
    - eth2
```

### `network.link.bridge`

Create or remove a runtime Linux bridge and enslave interfaces.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `interfaces` | no | `list` |  | Network interfaces to include in a bond or aggregate. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `stp` | no | `boolean` | `False` | Enable STP on a Linux bridge when supported. |
| `mtu` | no | `integer` |  | Network interface MTU. |
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
use: network.link.bridge
with:
  name: nginx
```

### `network.link.check`

Check that a network link exists and optionally has expected state or MTU.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `mtu` | no | `integer` |  | Network interface MTU. |
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
use: network.link.check
with:
  name: nginx
```

### `network.link.facts`

Gather network link facts from iproute2 JSON output.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.links`: Network link facts from iproute2 JSON output.

Example:

```yaml
use: network.link.facts
with:
  name: nginx
  sudo: true
```

### `network.link.interface`

Apply runtime and optional persistent interface state/address configuration.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `address` | no | `string` |  | IP address to configure. |
| `prefix` | no | `integer` |  | CIDR prefix length. |
| `gateway` | no | `string` |  | Route gateway address. |
| `mtu` | no | `integer` |  | Network interface MTU. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `backend` | no | `string` |  | Operation backend such as auto, runtime, networkmanager, systemd-networkd, ifcfg, plain-file, systemd-resolved or resolvconf. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: network.link.interface
with:
  name: nginx
```

### `network.link.vlan`

Create or update a runtime and optional persistent VLAN interface.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `parent` | yes | `string` |  | Parent network interface. |
| `vlan_id` | yes | `integer` |  | VLAN identifier. |
| `address` | no | `string` |  | IP address to configure. |
| `prefix` | no | `integer` |  | CIDR prefix length. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `backend` | no | `string` |  | Operation backend such as auto, runtime, networkmanager, systemd-networkd, ifcfg, plain-file, systemd-resolved or resolvconf. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: network.link.vlan
with:
  name: nginx
  parent: eth0
  vlan_id: 100
```

### `network.route.add`

Ensure a runtime and optional persistent IP route is present.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `dest` | yes | `path` |  | Destination path. |
| `gateway` | no | `string` |  | Route gateway address. |
| `dev` | no | `string` |  | Network device name for a route. |
| `table` | no | `string` |  | Routing table name or number. |
| `metric` | no | `integer` |  | Route metric. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `backend` | no | `string` |  | Operation backend such as auto, runtime, networkmanager, systemd-networkd, ifcfg, plain-file, systemd-resolved or resolvconf. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: network.route.add
with:
  dest: /tmp/dest
```

### `network.route.check`

Check that a route exists with optional gateway, device, table or metric.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `dest` | yes | `path` |  | Destination path. |
| `gateway` | no | `string` |  | Route gateway address. |
| `dev` | no | `string` |  | Network device name for a route. |
| `table` | no | `string` |  | Routing table name or number. |
| `metric` | no | `integer` |  | Route metric. |
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
use: network.route.check
with:
  dest: /tmp/dest
```

### `network.route.facts`

Gather IP route facts from iproute2 JSON output.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `family` | no | `string` | `inet` | nftables address family such as ip, ip6, inet, arp, bridge or netdev. |
| `table` | no | `string` |  | Routing table name or number. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.routes`: Route facts from iproute2 JSON output.

Example:

```yaml
use: network.route.facts
with:
  family: inet
  table: main
```

### `network.route.remove`

Ensure a runtime and optional persistent IP route is absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `dest` | yes | `path` |  | Destination path. |
| `gateway` | no | `string` |  | Route gateway address. |
| `dev` | no | `string` |  | Network device name for a route. |
| `table` | no | `string` |  | Routing table name or number. |
| `metric` | no | `integer` |  | Route metric. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `backend` | no | `string` |  | Operation backend such as auto, runtime, networkmanager, systemd-networkd, ifcfg, plain-file, systemd-resolved or resolvconf. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: network.route.remove
with:
  dest: /tmp/dest
```

## notify

### `notify.mail.send`

Send an email from the Automax controller through SMTP.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `smtp_host` | yes | `string` |  | SMTP server host used by the Automax controller. |
| `from` | yes | `string` |  | Source address for firewall rules. |
| `to` | yes | `string` |  | Email recipient or non-empty recipient list. |
| `subject` | yes | `string` |  | Email subject line. |
| `smtp_port` | no | `integer` | `587` | SMTP server port. |
| `starttls` | no | `boolean` | `True` | Use STARTTLS before SMTP authentication. |
| `ssl` | no | `boolean` | `False` | Use implicit TLS for SMTP. |
| `username` | no | `string` |  | SMTP username; prefer values rendered from secrets. |
| `password` | no | `string` |  | Plaintext password; prefer password_hash when possible. |
| `body` | no | `string` |  | Raw HTTP request body. |
| `cc` | no | `list` |  | Email CC recipient or non-empty recipient list. |
| `bcc` | no | `list` |  | Email BCC recipient or non-empty recipient list. |
| `reply_to` | no | `string` |  | Email Reply-To address. |
| `attachments` | no | `list` |  | Attachment path or attachment path list. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: notify.mail.send
with:
  smtp_host: smtp.example.com
  from: 10.0.0.0/8
  to: any
  subject: Automax notification
```

## os

### `os.alternatives.check`

Assert that one system alternative points to the expected path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
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
use: os.alternatives.check
with:
  name: nginx
  path: /tmp/automax-demo
```

### `os.alternatives.get`

Read the current alternatives configuration for one alternative name.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.alternatives.get
with:
  name: nginx
```

### `os.alternatives.list`

List known system alternatives across update-alternatives or alternatives implementations.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.alternatives.list
with:
  sudo: true
```

### `os.alternatives.set`

Set a system alternative using update-alternatives or alternatives.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
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
use: os.alternatives.set
with:
  name: nginx
  path: /tmp/automax-demo
```

### `os.arch.check`

Assert that the remote normalized architecture matches an allowed value.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `arch` | no | `string` | `b64` | CPU architecture selector for audit rules. |
| `any_of` | no | `list` |  | Allowed values for a check operation. |
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
use: os.arch.check
with:
  any_of:
    type: list
    description: Allowed values for a check operation.
```

### `os.capability.check`

Assert remote tools, paths and optional shell checks required by a job preflight.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `tools` | no | `list` |  | Executable names required by a capability preflight. |
| `paths` | no | `list` |  | Relative paths selected for manifest or inventory operations. |
| `commands` | no | `list` |  | Allowed sudo command list or ALL. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: os.capability.check
```

### `os.env.check`

Assert one environment variable value in the remote shell context.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `value` | yes | `string` |  | Desired parameter value. |
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
use: os.env.check
with:
  name: nginx
  value: 1
```

### `os.env.facts`

Read the remote shell environment as key/value facts.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.env.facts
with:
  sudo: true
```

### `os.env.get`

Read one environment variable from the remote shell context.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.env.get
with:
  name: nginx
```

### `os.env.remove`

Remove a managed persistent shell environment file or unset step-scoped variables.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `names` | no | `list` |  | Hostnames or aliases for a hosts entry. |
| `scope` | no | `string` | `step` | Environment scope: step, user, global or file. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |
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
use: os.env.remove
with:
  name: nginx
  names:
    - app1.example.com
    - app1
```

### `os.env.set`

Set step-scoped or persistent shell environment variables.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `variables` | yes | `mapping` |  | Environment variables to set. |
| `scope` | no | `string` | `step` | Environment scope: step, user, global or file. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `user` | no | `string` | `False` | User account name for scope=user. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.env.set
with:
  variables:
    APP_HOME: /opt/app
```

### `os.facts`

Gather remote operating-system, kernel, architecture and hostname facts.

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
use: os.facts
with:
  subset:
    - os
    - network
    - services
```

### `os.hostname.check`

Assert the current static hostname.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.hostname.check
with:
  name: nginx
```

### `os.hostname.get`

Read the current static hostname.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.hostname.get
with:
  sudo: true
```

### `os.hostname.set`

Set the system hostname with hostnamectl.

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
use: os.hostname.set
with:
  name: nginx
```

### `os.hosts.entry.add`

Ensure or remove an /etc/hosts entry with automatic pre-change backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `ip` | yes | `string` |  | IP address for a hosts entry. |
| `names` | yes | `list` |  | Hostnames or aliases for a hosts entry. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.hosts.entry.add
with:
  ip: 192.0.2.10
  names:
    - app1.example.com
    - app1
```

### `os.hosts.entry.check`

Assert that an exact /etc/hosts entry is present.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `ip` | yes | `string` |  | IP address for a hosts entry. |
| `names` | yes | `list` |  | Hostnames or aliases for a hosts entry. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.hosts.entry.check
with:
  ip: 192.0.2.10
  names:
    - app1.example.com
    - app1
```

### `os.hosts.entry.remove`

Remove an exact /etc/hosts entry with automatic pre-change backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `ip` | yes | `string` |  | IP address for a hosts entry. |
| `names` | yes | `list` |  | Hostnames or aliases for a hosts entry. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.hosts.entry.remove
with:
  ip: 192.0.2.10
  names:
    - app1.example.com
    - app1
```

### `os.hosts.facts`

Read /etc/hosts entries as structured facts.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: os.hosts.facts
with:
  path: /tmp/automax-demo
  sudo: true
```

### `os.limits.dropin`

Install an /etc/security/limits.d drop-in from structured entries.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `entries` | yes | `list` |  | Structured entries for limits or configuration files. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.limits.dropin
with:
  name: nginx
  entries:
    - {'domain': 'appuser', 'type': 'soft', 'item': 'nofile', 'value': 1024}
```

### `os.login.defs.check`

Assert /etc/login.defs settings.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `settings` | yes | `mapping` |  | SSH client or server settings. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: os.login.defs.check
with:
  settings: value
```

### `os.login.defs.get`

Read /etc/login.defs settings.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `key` | no | `string` |  | SSH public key line. |
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
use: os.login.defs.get
with:
  path: /tmp/automax-demo
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
```

### `os.login.defs.set`

Manage /etc/login.defs settings with backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `settings` | yes | `mapping` |  | SSH client or server settings. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.login.defs.set
with:
  settings: value
```

### `os.package.check`

Assert package installation state and optionally version.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `version` | no | `string` |  | Package version to pin. |
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
use: os.package.check
with:
  name: nginx
```

### `os.package.clean`

Clean package-manager caches.

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

Example:

```yaml
use: os.package.clean
with:
  manager: auto
  sudo: true
```

### `os.package.facts`

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
use: os.package.facts
with:
  manager: auto
  sudo: true
```

### `os.package.files`

List files installed by a package.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
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
use: os.package.files
with:
  name: nginx
```

### `os.package.hold.add`

Hold or lock package versions with the native package manager.

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
use: os.package.hold.add
with:
  name: nginx
  packages:
    - curl
```

### `os.package.hold.check`

Assert package hold state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
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
use: os.package.hold.check
with:
  name: nginx
```

### `os.package.hold.list`

List packages currently held by the package manager.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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

Example:

```yaml
use: os.package.hold.list
with:
  manager: auto
  sudo: true
```

### `os.package.hold.remove`

Remove package holds or version locks.

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
use: os.package.hold.remove
with:
  name: nginx
  packages:
    - curl
```

### `os.package.install`

Install packages on a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `version` | no | `string` |  | Package version to pin. |
| `enablerepo` | no | `list` |  | Temporary repository to enable for package operation. |
| `disablerepo` | no | `list` |  | Temporary repository to disable for package operation. |
| `no_recommends` | no | `boolean` | `False` | Disable recommended dependencies where supported. |
| `lock_after_install` | no | `boolean` | `False` | Lock package after installation. |
| `allow_downgrade` | no | `boolean` | `False` | Allow explicit package downgrades. |
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
use: os.package.install
with:
  name: nginx
  packages:
    - curl
```

### `os.package.key.add`

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
use: os.package.key.add
with:
  name: vendor
  manager: apt
  url: https://repo.example/key.gpg
  sudo: true
```

### `os.package.key.check`

Assert a package repository signing key file exists.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.package.key.check
with:
  name: nginx
```

### `os.package.key.list`

List package repository signing key files.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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

Example:

```yaml
use: os.package.key.list
with:
  manager: auto
  sudo: true
```

### `os.package.key.remove`

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
use: os.package.key.remove
with:
  name: nginx
```

### `os.package.owner`

Report which package owns a file path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
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
use: os.package.owner
with:
  path: /tmp/automax-demo
```

### `os.package.query`

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
use: os.package.query
with:
  name: nginx
  packages:
    - curl
```

### `os.package.remove`

Remove packages from a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `packages` | no | `list` |  | Package names for package-manager operations. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `purge` | no | `boolean` | `False` | Remove package configuration where supported. |
| `autoremove` | no | `boolean` | `False` | Remove unused dependencies where supported. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
| `protect_packages` | no | `list` |  | Packages that must not be removed. |
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
use: os.package.remove
with:
  name: nginx
  packages:
    - curl
```

### `os.package.repo.add`

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
use: os.package.repo.add
with:
  name: vendor
  manager: apt
  repo: deb [signed-by=/etc/apt/keyrings/vendor.gpg] https://repo.example stable main
  update_cache: true
  sudo: true
```

### `os.package.repo.check`

Assert a package repository definition file exists and optionally contains text.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `dest` | no | `path` |  | Destination path. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |
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
use: os.package.repo.check
with:
  name: nginx
```

### `os.package.repo.list`

List package repository definition files.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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

Example:

```yaml
use: os.package.repo.list
with:
  manager: auto
  sudo: true
```

### `os.package.repo.priority.check`

Assert a package repository priority drop-in exists with expected content.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `priority` | yes | `integer` |  | Package repository or pin priority. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `file` | no | `path` |  | Remote configuration file path. |
| `content` | no | `string` |  | Text content to write. |
| `baseurl` | no | `string` |  | Repository base URL for package manager repository files. |
| `enabled` | no | `boolean` | `True` | Whether a repository or persistent resource is enabled. |
| `gpgcheck` | no | `boolean` | `True` | Whether repository GPG checking is enabled. |
| `gpgkey` | no | `string` |  | Repository GPG key URL or path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.package.repo.priority.check
with:
  name: nginx
  priority: 1001
```

### `os.package.repo.priority.set`

Install package repository priority or pinning configuration for apt, dnf/yum or zypper.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `priority` | yes | `integer` |  | Package repository or pin priority. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `file` | no | `path` |  | Remote configuration file path. |
| `content` | no | `string` |  | Text content to write. |
| `baseurl` | no | `string` |  | Repository base URL for package manager repository files. |
| `enabled` | no | `boolean` | `True` | Whether a repository or persistent resource is enabled. |
| `gpgcheck` | no | `boolean` | `True` | Whether repository GPG checking is enabled. |
| `gpgkey` | no | `string` |  | Repository GPG key URL or path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.package.repo.priority.set
with:
  name: nginx
  priority: 1001
```

### `os.package.repo.remove`

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
use: os.package.repo.remove
with:
  name: nginx
```

### `os.package.update_cache`

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
use: os.package.update_cache
with:
  name: nginx
  packages:
    - curl
```

### `os.package.upgrade`

Upgrade remote packages.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `security_only` | no | `boolean` | `False` | Apply only security updates where supported. |
| `exclude` | no | `list` |  | Package or archive excludes. |
| `download_only` | no | `boolean` | `False` | Download packages without installing. |
| `reboot_required_check` | no | `boolean` | `False` | Check whether reboot is required after package operation. |
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
use: os.package.upgrade
with:
  manager: auto
```

### `os.package.verify`

Verify installed package file integrity when the package manager supports it.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.package.verify
with:
  name: nginx
  packages:
    - curl
```

### `os.package.version.check`

Assert that an installed package version matches the expected version.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `version` | yes | `string` |  | Package version to pin. |
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
use: os.package.version.check
with:
  name: nginx
  version: 1.2.3*
```

### `os.package.version.pin`

Pin a package version using the native package-manager mechanism.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `version` | yes | `string` |  | Package version to pin. |
| `manager` | no | `string` | `auto` | Package manager: auto, apt, dnf, yum, zypper or pacman. |
| `priority` | no | `integer` |  | Package repository or pin priority. |
| `file` | no | `path` |  | Remote configuration file path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.package.version.pin
with:
  name: nginx
  version: 1.2.3*
```

### `os.platform.facts`

Collect portable Linux backend facts for package, service, network, resolver and trust-store operations.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.platform.facts
with:
  sudo: true
```

### `os.time.chrony.servers.check`

Assert configured chrony server lines in the managed chrony drop-in.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `servers` | yes | `list` |  | NTP/chrony server names. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: os.time.chrony.servers.check
with:
  servers:
    - time.example.com
```

### `os.time.chrony.servers.get`

Read configured chrony server lines from chrony configuration.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: os.time.chrony.servers.get
with:
  path: /tmp/automax-demo
  sudo: true
```

### `os.time.chrony.servers.set`

Install a chrony server drop-in and optionally restart chronyd.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `servers` | yes | `list` |  | NTP/chrony server names. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: os.time.chrony.servers.set
with:
  servers:
    - time.example.com
```

### `os.time.chrony.sources.check`

Assert chrony has usable sources and print tracking/source status.

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
use: os.time.chrony.sources.check
with:
  sudo: true
```

### `os.time.chrony.tracking.check`

Assert chrony tracking health using chronyc tracking.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `max_offset` | no | `number` | `1.0` | Maximum allowed NTP/chrony offset in seconds. |
| `max_stratum` | no | `integer` | `16` | Maximum allowed NTP/chrony stratum. |
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
use: os.time.chrony.tracking.check
```

### `os.time.ntp.check`

Assert whether timedatectl NTP synchronization is enabled.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `enabled` | yes | `boolean` | `True` | Whether a repository or persistent resource is enabled. |
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
use: os.time.ntp.check
with:
  enabled: value
```

### `os.time.ntp.get`

Read whether timedatectl NTP synchronization is enabled.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.time.ntp.get
with:
  sudo: true
```

### `os.time.ntp.set`

Enable or disable NTP through timedatectl.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `enabled` | yes | `boolean` | `True` | Whether a repository or persistent resource is enabled. |
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
use: os.time.ntp.set
with:
  enabled: value
```

### `os.time.status`

Read timedatectl time, timezone and NTP state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.time.status
with:
  sudo: true
```

### `os.time.timezone.check`

Assert the current system timezone with timedatectl.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `timezone` | yes | `string` |  | IANA timezone name. |
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
use: os.time.timezone.check
with:
  timezone: value
```

### `os.time.timezone.get`

Read the current system timezone with timedatectl.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: os.time.timezone.get
with:
  sudo: true
```

### `os.time.timezone.set`

Set system timezone with timedatectl.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `timezone` | yes | `string` |  | IANA timezone name. |
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
use: os.time.timezone.set
with:
  timezone: value
```

### `os.tool.check`

Assert that one executable exists on the remote PATH.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: os.tool.check
with:
  name: nginx
```

### `os.tool.version_check`

Assert that a remote tool version output contains or matches the expected value.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `version_arg` | no | `string` | `--version` | Argument used to print a tool version. |
| `contains` | no | `string` |  | Required substring in stdout or HTTP response body. |
| `regex` | no | `string` |  | Regular expression expected in command output. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: os.tool.version_check
with:
  name: nginx
```

## security

### `security.apparmor.complain`

Put one AppArmor profile in complain mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile, authselect profile or profile file path. |
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
use: security.apparmor.complain
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
```

### `security.apparmor.disable`

Disable one AppArmor profile after explicit confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile, authselect profile or profile file path. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: security.apparmor.disable
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
```

### `security.apparmor.enforce`

Put one AppArmor profile in enforcing mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile, authselect profile or profile file path. |
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
use: security.apparmor.enforce
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
```

### `security.apparmor.profile`

Set an AppArmor profile to enforce or complain mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile, authselect profile or profile file path. |
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
use: security.apparmor.profile
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
  state: enforce
  sudo: true
```

### `security.apparmor.profile_check`

Assert that an AppArmor profile is loaded in the expected mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile, authselect profile or profile file path. |
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
use: security.apparmor.profile_check
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
  state: present
```

### `security.apparmor.reload`

Reload one AppArmor profile file or the AppArmor service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | no | `string` |  | AppArmor profile, authselect profile or profile file path. |
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
use: security.apparmor.reload
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
  sudo: true
```

### `security.apparmor.status`

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
use: security.apparmor.status
with:
  sudo: true
```

### `security.apparmor.validate`

Validate an AppArmor profile with apparmor_parser before applying it.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile, authselect profile or profile file path. |
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
use: security.apparmor.validate
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
```

### `security.audit.backlog_check`

Assert auditd lost-event count and backlog are below thresholds.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `max_lost` | no | `integer` | `0` | Maximum allowed audit lost-event count. |
| `max_backlog` | no | `integer` | `8192` | Maximum allowed audit backlog. |
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
use: security.audit.backlog_check
```

### `security.audit.reload`

Reload auditd rules using augenrules or the auditd service.

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
use: security.audit.reload
with:
  sudo: true
```

### `security.audit.rule`

Install an auditd rules.d drop-in with backup and optional reload.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `rule` | no | `string` |  | Firewall action such as allow, deny, reject or limit. |
| `rules` | no | `list` |  | Structured rule entries. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.audit.rule
with:
  name: nginx
```

### `security.audit.rules.facts`

List active auditd rules and persistent rules.d files.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: security.audit.rules.facts
with:
  sudo: true
```

### `security.audit.search`

Search audit events by key, user or time window.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `key` | no | `string` |  | Audit event key. |
| `user` | no | `string` |  | Audit user name or numeric UID. |
| `start` | no | `string` |  | Audit search start time. |
| `end` | no | `string` |  | Audit search end time. |
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
use: security.audit.search
with:
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
  user: deploy
```

### `security.audit.status`

Read auditd status without changing the system.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: security.audit.status
with:
  sudo: true
```

### `security.audit.syscall`

Install an auditd syscall rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `syscalls` | yes | `list` |  | Audit syscall names. |
| `key` | yes | `string` |  | SSH public key line. |
| `arch` | no | `string` | `b64` | CPU architecture selector for audit rules. |
| `action` | no | `string` |  | udev action to trigger. |
| `filters` | no | `list` |  | Audit rule filters such as auid>=1000. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.audit.syscall
with:
  name: nginx
  syscalls: value
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
```

### `security.audit.watch`

Install an auditd filesystem watch rule.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `permissions` | yes | `string` |  | Audit permissions such as rwa or wa. |
| `key` | yes | `string` |  | SSH public key line. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.audit.watch
with:
  name: nginx
  path: /tmp/automax-demo
  permissions: value
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
```

### `security.authselect.check`

Assert the current authselect profile and enabled features on RHEL-like systems.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | no | `string` |  | AppArmor profile, authselect profile or profile file path. |
| `features` | no | `list` |  | Profile or backend feature flags. |
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
use: security.authselect.check
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
```

### `security.authselect.profile`

Select an authselect profile with optional features and backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile, authselect profile or profile file path. |
| `features` | no | `list` |  | Profile or backend feature flags. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: security.authselect.profile
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
```

### `security.pam.access`

Manage access.conf entries and optional pam_access service wiring.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `entries` | yes | `list` |  | Structured entries for limits or configuration files. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `services` | no | `list` |  | PAM service names to inspect or modify. |
| `service_files` | no | `list` |  | Explicit PAM service file paths to inspect or modify. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.pam.access
with:
  entries:
    - {'domain': 'appuser', 'type': 'soft', 'item': 'nofile', 'value': 1024}
```

### `security.pam.backup`

Backup one PAM service file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: security.pam.backup
with:
  service: sshd
```

### `security.pam.faillock`

Manage faillock.conf settings and optional pam_faillock service wiring.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `settings` | yes | `mapping` |  | SSH client or server settings. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `services` | no | `list` |  | PAM service names to inspect or modify. |
| `service_files` | no | `list` |  | Explicit PAM service file paths to inspect or modify. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.pam.faillock
with:
  settings: value
```

### `security.pam.include_check`

Assert a PAM service includes another stack.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `include` | yes | `string` |  | PAM include/substack target name. |
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
use: security.pam.include_check
with:
  service: sshd
  include: value
```

### `security.pam.limits`

Ensure pam_limits.so is enabled in one or more PAM service files.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `files` | no | `list` |  | Target files to inspect or modify. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.pam.limits
with:
  files:
    - /etc/pam.d/login
```

### `security.pam.module_check`

Assert a PAM module line exists in a service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `module` | yes | `string` |  | Linux kernel module name. |
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
use: security.pam.module_check
with:
  service: sshd
  module: br_netfilter
```

### `security.pam.order_check`

Assert one PAM line appears before another.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `before` | yes | `string` |  | Marker that must appear before another line or rule. |
| `after` | yes | `string` |  | Marker that must appear after another line or rule. |
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
use: security.pam.order_check
with:
  service: sshd
  before: value
  after: value
```

### `security.pam.pwhistory`

Manage pwhistory.conf settings and optional pam_pwhistory service wiring.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `settings` | yes | `mapping` |  | SSH client or server settings. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `services` | no | `list` |  | PAM service names to inspect or modify. |
| `service_files` | no | `list` |  | Explicit PAM service file paths to inspect or modify. |
| `control` | no | `string` |  | PAM control field such as required, requisite, sufficient or a bracketed control expression. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.pam.pwhistory
with:
  settings: value
```

### `security.pam.restore`

Restore one PAM service file from backup after confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `src` | yes | `path` |  | Source path. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: security.pam.restore
with:
  service: sshd
  src: /tmp/source
```

### `security.pam.service_line`

Ensure or remove one exact line in one PAM service file with backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `line` | yes | `string` |  | Exact line to ensure in a remote file. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.pam.service_line
with:
  service: sshd
  line: KEY=value
```

### `security.pam.stack.facts`

Inventory PAM service files and include/substack relationships.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `services` | no | `list` |  | PAM service names to inspect or modify. |
| `service_files` | no | `list` |  | Explicit PAM service file paths to inspect or modify. |
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
use: security.pam.stack.facts
with:
  service: sshd
  services:
    - sshd
```

### `security.pam.succeed_if`

Ensure or remove one guarded pam_succeed_if condition in a PAM service file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `condition` | yes | `string` |  | PAM condition expression, for example user ingroup wheel. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `control` | no | `string` |  | PAM control field such as required, requisite, sufficient or a bracketed control expression. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.pam.succeed_if
with:
  service: sshd
  condition: user ingroup wheel
```

### `security.pam.validate`

Run read-only sanity checks against explicit PAM service files.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `services` | no | `list` |  | PAM service names to inspect or modify. |
| `service_files` | no | `list` |  | Explicit PAM service file paths to inspect or modify. |
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
use: security.pam.validate
with:
  service: sshd
  services:
    - sshd
```

### `security.password.policy`

Install a pwquality password policy drop-in.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | pwquality drop-in filename, with .conf appended when omitted. |
| `settings` | yes | `mapping` |  | pwquality.conf key/value settings such as minlen, dcredit, ucredit or retry. |
| `path` | no | `path` |  | Explicit pwquality drop-in path; defaults to /etc/security/pwquality.conf.d/<name>.conf. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.password.policy
with:
  name: hardening
  settings:
    minlen: 14
    dcredit: -1
    ucredit: -1
    retry: 3
  sudo: true
```

### `security.pki.cert.chain_check`

Verify a certificate chain against a CA bundle with openssl verify.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `ca_file` | yes | `path` |  | CA bundle file path. |
| `untrusted` | no | `path` |  | Untrusted intermediate certificate chain file. |
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
use: security.pki.cert.chain_check
with:
  cert: value
  ca_file: value
```

### `security.pki.cert.expiry_check`

Assert that a certificate remains valid for at least min_days.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `min_days` | no | `integer` | `30` | Minimum remaining certificate validity in days. |
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
use: security.pki.cert.expiry_check
with:
  path: /tmp/automax-demo
```

### `security.pki.cert.expiry_report`

Report certificate expiry and optionally fail inside a warning window.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `warning_days` | no | `integer` | `30` | Certificate expiry warning window in days. |
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
use: security.pki.cert.expiry_report
with:
  cert: value
```

### `security.pki.cert.fingerprint`

Read a certificate fingerprint with openssl.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `algorithm` | no | `string` | `sha256` | Fingerprint or checksum algorithm name. |
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
use: security.pki.cert.fingerprint
with:
  cert: value
```

### `security.pki.cert.install_keypair`

Install a certificate and private key with safe permissions and optional validation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `key` | yes | `string` |  | SSH public key line. |
| `cert_dest` | yes | `path` |  | Installed certificate destination path. |
| `key_dest` | yes | `path` |  | Installed private key destination path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `validate` | no | `boolean` | `True` | Validate generated or uploaded content before installing it. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
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
use: security.pki.cert.install_keypair
with:
  cert: value
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
  cert_dest: value
  key_dest: value
```

### `security.pki.cert.issuer_check`

Assert that a certificate issuer contains an expected string.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `issuer` | yes | `string` |  | Expected certificate issuer string. |
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
use: security.pki.cert.issuer_check
with:
  cert: value
  issuer: CN=Example CA
```

### `security.pki.cert.key_match_check`

Assert that a certificate public key matches a private key.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `key` | yes | `string` |  | SSH public key line. |
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
use: security.pki.cert.key_match_check
with:
  cert: value
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
```

### `security.pki.cert.san_check`

Assert that a certificate contains required Subject Alternative Names.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `names` | yes | `list` |  | Hostnames or aliases for a hosts entry. |
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
use: security.pki.cert.san_check
with:
  cert: value
  names:
    - app1.example.com
    - app1
```

### `security.pki.cert.self_signed`

Generate a self-signed certificate using an existing private key.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `key` | yes | `string` |  | SSH public key line. |
| `cert` | yes | `path` |  | Certificate path. |
| `subject` | yes | `string` |  | Email subject line. |
| `days` | no | `integer` | `365` | Certificate validity in days. |
| `extensions` | no | `string` |  | OpenSSL extension section name. |
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
use: security.pki.cert.self_signed
with:
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
  cert: value
  subject: Automax notification
```

### `security.pki.cert.subject_check`

Assert that a certificate subject contains an expected string.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `cert` | yes | `path` |  | Certificate path. |
| `subject` | yes | `string` |  | Email subject line. |
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
use: security.pki.cert.subject_check
with:
  cert: value
  subject: Automax notification
```

### `security.pki.csr.generate`

Generate a CSR from an existing private key using openssl.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `key` | yes | `string` |  | SSH public key line. |
| `dest` | yes | `path` |  | Destination path. |
| `subject` | yes | `string` |  | Email subject line. |
| `config` | no | `path` |  | OpenSSL configuration file path. |
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
use: security.pki.csr.generate
with:
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
  dest: /tmp/dest
  subject: Automax notification
```

### `security.pki.key.permissions`

Enforce owner/group/mode on a private key or certificate file.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
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
use: security.pki.key.permissions
with:
  path: /tmp/automax-demo
```

### `security.pki.trust.install_bundle`

Install a CA bundle file with safe permissions and optional trust-store refresh.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `update_trust` | no | `boolean` | `True` | Refresh the system trust store after installing a CA certificate. |
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
use: security.pki.trust.install_bundle
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `security.pki.trust.install_ca`

Install a CA certificate into an explicit path or a distro-native system trust store.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `dest` | no | `path` |  | Destination path. |
| `name` | no | `string` |  | Package, user or group name. |
| `trust_store` | no | `string` | `explicit` | Trust-store mode: explicit path or system auto path. |
| `src` | no | `path` |  | Source path. |
| `content` | no | `string` |  | Text content to write. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `update_trust` | no | `boolean` | `True` | Refresh the system trust store after installing a CA certificate. |
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
use: security.pki.trust.install_ca
with:
  dest: /tmp/dest
  name: nginx
```

### `security.secret.redact_check`

Assert that a payload contains no declared secret values after redaction policy is applied.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `text` | no | `string` |  | Text payload for redaction scanning or assertion. |
| `value` | no | `string` |  | Desired parameter value. |
| `source` | no | `path` |  | Remote source path to archive. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: security.secret.redact_check
with:
  text: password=secret
  value: 1
```

### `security.secret.scan_output`

Scan an arbitrary output payload and report whether redaction would change it.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `text` | no | `string` |  | Text payload for redaction scanning or assertion. |
| `value` | no | `string` |  | Desired parameter value. |
| `source` | no | `path` |  | Remote source path to archive. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: security.secret.scan_output
with:
  text: password=secret
  value: 1
```

### `security.secret.scan_preview`

Scan preview/manual-command text with the same redaction policy used by the engine.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `text` | no | `string` |  | Text payload for redaction scanning or assertion. |
| `value` | no | `string` |  | Desired parameter value. |
| `source` | no | `path` |  | Remote source path to archive. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: security.secret.scan_preview
with:
  text: password=secret
  value: 1
```

### `security.selinux.boolean`

Set an SELinux boolean.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `value` | yes | `string` |  | Desired SELinux boolean value. |
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
use: security.selinux.boolean
with:
  name: httpd_can_network_connect
  value: true
  persist: true
  sudo: true
```

### `security.selinux.context`

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
use: security.selinux.context
with:
  path: /tmp/automax-demo
  selinux_type: httpd_sys_content_t
```

### `security.selinux.fcontext`

Manage a persistent SELinux fcontext mapping with semanage fcontext.

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
use: security.selinux.fcontext
with:
  path: /tmp/automax-demo
  selinux_type: httpd_sys_content_t
```

### `security.selinux.mode`

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
use: security.selinux.mode
with:
  state: present
```

### `security.selinux.port`

Manage a persistent SELinux port type mapping with semanage port.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `port` | yes | `integer` |  | TCP port number. |
| `protocol` | yes | `string` | `tcp` | Network protocol such as tcp or udp. |
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
use: security.selinux.port
with:
  port: 22
  protocol: tcp
  selinux_type: httpd_sys_content_t
```

### `security.selinux.restorecon`

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
use: security.selinux.restorecon
with:
  path: /tmp/automax-demo
```

### `security.ssh.authorized_key.add`

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
| `key_options` | no | `string` |  | SSH authorized_keys options prefix. |
| `exclusive` | no | `boolean` | `False` | Keep only managed entries where supported. |
| `comment_update` | no | `string` |  | Authorized key comment to write. |
| `fingerprint_assert` | no | `string` |  | Expected fingerprint value. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: security.ssh.authorized_key.add
with:
  user: deploy
  key: '{{ vars.deploy_public_key }}'
  state: present
  sudo: true
```

### `security.ssh.authorized_key.remove`

Remove one SSH authorized_keys line for a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | Remote user account owning authorized_keys. |
| `key` | yes | `string` |  | SSH public key line. |
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
use: security.ssh.authorized_key.remove
with:
  user: deploy
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
```

### `security.ssh.config`

Install SSH client or sshd config drop-ins with backup and optional reload.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `settings` | yes | `mapping` |  | SSH client or server settings. |
| `scope` | no | `string` | `step` | Environment scope: step, user, global or file. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `match` | no | `string` |  | SSH Match clause. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.ssh.config
with:
  name: nginx
  settings: value
```

### `security.ssh.fingerprint`

Read an SSH public or private key fingerprint with ssh-keygen.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `algorithm` | no | `string` | `sha256` | Fingerprint or checksum algorithm name. |
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
use: security.ssh.fingerprint
with:
  path: /tmp/automax-demo
```

### `security.ssh.host_keygen`

Generate missing OpenSSH host keys on a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `types` | no | `list` |  | SSH key types or other typed values accepted by the plugin. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: security.ssh.host_keygen
with:
  types:
    - ed25519
  force: true
```

### `security.ssh.keygen`

Generate an SSH keypair on a remote target with idempotent overwrite protection.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
| `bits` | no | `integer` |  | Key size in bits when supported by the selected key type. |
| `comment` | no | `string` |  | User account comment or GECOS field. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `passphrase_secret` | no | `string` |  | Secret name containing a key passphrase. |
| `public_key_only` | no | `boolean` | `False` | Only derive/read the public key instead of generating a new keypair. |
| `fingerprint` | no | `boolean` | `True` | Emit a key or certificate fingerprint after the operation. |
| `algorithm` | no | `string` | `sha256` | Fingerprint or checksum algorithm name. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |
| `owner` | no | `string` |  | Remote file owner. |
| `group` | no | `string` |  | Primary group, file group owner or remote group name. |
| `mode` | no | `string` |  | POSIX file mode, for example 0644 or 0755. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: security.ssh.keygen
with:
  path: /tmp/automax-demo
```

### `security.ssh.known_hosts`

Ensure a known_hosts entry exists or is removed on a remote target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `host` | yes | `string` |  | Hostname or IP address to check from the controller. |
| `key` | no | `string` |  | SSH public key line. |
| `port` | no | `integer` |  | TCP port number. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `user` | no | `string` | `False` | Remote user account owning known_hosts. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.ssh.known_hosts
with:
  host: 127.0.0.1
```

### `security.ssh.public_key`

Derive or read an SSH public key from a private key path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `dest` | no | `path` |  | Destination path. |
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
use: security.ssh.public_key
with:
  path: /tmp/automax-demo
```

### `security.sshd.config`

Install an sshd_config.d hardening drop-in with sshd syntax validation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `settings` | yes | `mapping` |  | SSH client or server settings. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `validate_before_reload` | no | `boolean` | `True` | Validate service configuration before reload. |
| `match_blocks` | no | `list` |  | OpenSSH Match blocks to render. |
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
use: security.sshd.config
with:
  name: nginx
  settings: value
```

### `security.sshd.validate`

Validate sshd configuration with sshd -t.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `config` | no | `path` |  | OpenSSL configuration file path. |
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
use: security.sshd.validate
with:
  sudo: true
```

### `security.sudo.can_run`

Assert that a user can run a command via sudo without prompting.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
| `command` | yes | `string` |  | Command line to execute. |
| `run_as` | no | `string` |  | sudo run-as target user. |
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
use: security.sudo.can_run
with:
  user: deploy
  command: echo automax
```

### `security.sudo.check`

Assert sudo -l output contains a rule fragment.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
| `rule` | yes | `string` |  | Firewall action such as allow, deny, reject or limit. |
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
use: security.sudo.check
with:
  user: deploy
  rule: allow
```

### `security.sudo.dropin`

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
use: security.sudo.dropin
with:
  name: deploy-myapp
  content: 'deploy ALL=(root) /bin/systemctl restart myapp'
  validate: true
  sudo: true
```

### `security.sudo.list`

List sudo privileges for a user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `string` | `False` | User account name. |
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
use: security.sudo.list
with:
  user: deploy
```

### `security.sudo.rule`

Install a structured sudoers.d rule with visudo validation, backup and safe mode.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `subject` | yes | `string` |  | Email subject line. |
| `hosts` | no | `string` | `ALL` | sudoers hosts field. |
| `runas` | no | `string` | `ALL` | sudoers run-as field. |
| `commands` | no | `list` |  | Allowed sudo command list or ALL. |
| `nopassword` | no | `boolean` | `False` | Whether to include NOPASSWD. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: security.sudo.rule
with:
  name: nginx
  subject: Automax notification
```

### `security.sudo.validate`

Validate sudoers syntax with visudo without changing files.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: security.sudo.validate
with:
  path: /tmp/automax-demo
  sudo: true
```

## storage

### `storage.block.empty_check`

Check that a block device has no detectable signature before destructive use.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
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
use: storage.block.empty_check
with:
  device: /dev/sdb
```

### `storage.block.facts`

Collect remote block-device facts with lsblk, blkid, udevadm and optional multipath output.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `devices` | no | `list` |  | Block devices to inspect. |
| `multipath` | no | `boolean` | `False` | Include multipath output when collecting block-device facts. |
| `udev` | no | `boolean` | `True` | Include udev properties when collecting facts. |
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
use: storage.block.facts
with:
  devices:
    - /dev/sdb
  multipath: false
```

### `storage.block.identity`

Read a stable block-device identifier with scsi_id and udevadm.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `scsi_id_path` | no | `path` | `/usr/lib/udev/scsi_id` | Path to the scsi_id helper. |
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
use: storage.block.identity
with:
  device: /dev/sdb
```

### `storage.block.mount_check`

Check that a block device is mounted at a path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
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
use: storage.block.mount_check
with:
  device: /dev/sdb
  path: /tmp/automax-demo
```

### `storage.block.not_mounted_check`

Check that a block device is not mounted.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
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
use: storage.block.not_mounted_check
with:
  device: /dev/sdb
```

### `storage.block.partition.apply`

Conservatively create a partition table and missing partitions with parted.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `label` | yes | `string` |  | Disk label, filesystem label or partition label. |
| `partitions` | yes | `list` |  | Desired partition entries for a storage.block.partition.apply operation. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_path` | no | `path` |  | Explicit backup path for pre-change file content. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
| `udev_settle` | no | `boolean` | `True` | Wait for udev events to settle after the operation. |
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
use: storage.block.partition.apply
with:
  device: /dev/sdb
  label: gpt
  partitions:
    - {'number': 1, 'name': 'DATA01', 'start': '1MiB', 'end': '100%'}
```

### `storage.block.partition.scan`

Reread one remote partition table with partprobe/blockdev and udev settle.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `udev_settle` | no | `boolean` | `True` | Wait for udev events to settle after the operation. |
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
use: storage.block.partition.scan
with:
  device: /dev/sdb
```

### `storage.block.scan`

Rescan remote SCSI hosts or one block device and optionally refresh multipath.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | no | `path` |  | Block device path. |
| `udev_settle` | no | `boolean` | `True` | Wait for udev events to settle after the operation. |
| `multipath_reload` | no | `boolean` | `False` | Refresh multipath maps after the operation. |
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
use: storage.block.scan
with:
  device: /dev/sdb
  udev_settle: true
```

### `storage.block.signatures.wipe`

Wipe block-device signatures with wipefs after an optional pre-change signature backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_path` | no | `path` |  | Explicit backup path for pre-change file content. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: storage.block.signatures.wipe
with:
  device: /dev/sdb
```

### `storage.block.size_check`

Check block device size in bytes.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `size` | yes | `string` |  | Size such as 16G for file-backed swap. |
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
use: storage.block.size_check
with:
  device: /dev/sdb
  size: 16G
```

### `storage.fs.check`

Check block-device identity fields reported by blkid.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `fstype` | no | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
| `label` | no | `string` |  | Disk label, filesystem label or partition label. |
| `uuid` | no | `string` |  | Filesystem or block-device UUID. |
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
use: storage.fs.check
with:
  device: /dev/sdb
```

### `storage.fs.create`

Create a filesystem on a block device, refusing existing signatures unless force is true.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `fstype` | yes | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
| `label` | no | `string` |  | Disk label, filesystem label or partition label. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: storage.fs.create
with:
  device: /dev/sdb
  fstype: xfs
```

### `storage.fs.facts`

Collect filesystem identity, mount and usage facts for a device or path.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | no | `path` |  | Block device path. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: storage.fs.facts
with:
  device: /dev/sdb
  path: /tmp/automax-demo
```

### `storage.fs.resize`

Resize a filesystem using the appropriate platform tool.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `fstype` | yes | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: storage.fs.resize
with:
  device: /dev/sdb
  fstype: xfs
```

### `storage.fstab.add`

Ensure an /etc/fstab entry is present.

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
use: storage.fstab.add
with:
  src: /dev/vdb1
  path: /data
  fstype: xfs
  opts: defaults,noatime
  sudo: true
```

### `storage.fstab.check`

Assert an fstab entry exists for source, path or fstype.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `source` | no | `path` |  | Remote source path to archive. |
| `fstype` | no | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
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
use: storage.fstab.check
with:
  path: /tmp/automax-demo
  source: /var/log/app
```

### `storage.fstab.remove`

Remove fstab entries matching a mountpoint or source after confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `source` | no | `path` |  | Remote source path to archive. |
| `file` | no | `path` |  | Remote configuration file path. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: storage.fstab.remove
with:
  path: /tmp/automax-demo
  source: /var/log/app
```

### `storage.fstab.validate`

Validate fstab syntax and optionally dry-run mount resolution.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: storage.fstab.validate
with:
  file: /etc/sysctl.d/99-automax.conf
  sudo: true
```

### `storage.lvm.facts`

Collect LVM PV, VG and LV facts from a target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `vg` | no | `string` |  | LVM volume group name. |
| `name` | no | `string` |  | Package, user or group name. |
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
use: storage.lvm.facts
with:
  vg: vg_app
  name: nginx
```

### `storage.lvm.lv.add`

Ensure an LVM logical volume exists, optionally formatting it when newly created.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `vg` | yes | `string` |  | LVM volume group name. |
| `name` | yes | `string` |  | Package, user or group name. |
| `size` | yes | `string` |  | Size such as 16G for file-backed swap. |
| `fstype` | no | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
| `resizefs` | no | `boolean` | `True` | Resize the filesystem along with the block/LVM operation. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: storage.lvm.lv.add
with:
  vg: vg_app
  name: nginx
  size: 16G
```

### `storage.lvm.lv.check`

Assert that an LVM logical volume exists and optionally matches a requested size.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `vg` | yes | `string` |  | LVM volume group name. |
| `name` | yes | `string` |  | Package, user or group name. |
| `size` | no | `string` |  | Size such as 16G for file-backed swap. |
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
use: storage.lvm.lv.check
with:
  vg: vg_app
  name: nginx
```

### `storage.lvm.lv.extend`

Extend an LVM logical volume, optionally resizing the filesystem.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `vg` | yes | `string` |  | LVM volume group name. |
| `name` | yes | `string` |  | Package, user or group name. |
| `size` | yes | `string` |  | Size such as 16G for file-backed swap. |
| `resizefs` | no | `boolean` | `True` | Resize the filesystem along with the block/LVM operation. |
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
use: storage.lvm.lv.extend
with:
  vg: vg_app
  name: nginx
  size: 16G
```

### `storage.lvm.lv.remove`

Remove an LVM logical volume with an explicit confirm flag.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `confirm` | yes | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: storage.lvm.lv.remove
with:
  path: /tmp/automax-demo
  confirm: value
```

### `storage.lvm.lv.scan`

Scan LVM logical volumes.

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
use: storage.lvm.lv.scan
with:
  sudo: true
```

### `storage.lvm.lv.snapshot`

Create an idempotent LVM snapshot logical volume.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `vg` | yes | `string` |  | LVM volume group name. |
| `source` | yes | `path` |  | Remote source path to archive. |
| `name` | yes | `string` |  | Package, user or group name. |
| `size` | yes | `string` |  | Size such as 16G for file-backed swap. |
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
use: storage.lvm.lv.snapshot
with:
  vg: vg_app
  source: /var/log/app
  name: nginx
  size: 16G
```

### `storage.lvm.lv.thin_pool`

Ensure an LVM thin pool exists.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `vg` | yes | `string` |  | LVM volume group name. |
| `name` | yes | `string` |  | Package, user or group name. |
| `size` | yes | `string` |  | Size such as 16G for file-backed swap. |
| `metadata_size` | no | `string` |  | LVM thin-pool metadata size. |
| `chunksize` | no | `string` |  | LVM thin-pool chunk size. |
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
use: storage.lvm.lv.thin_pool
with:
  vg: vg_app
  name: nginx
  size: 16G
```

### `storage.lvm.pv.add`

Ensure a block device is initialized as an LVM physical volume.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: storage.lvm.pv.add
with:
  device: /dev/sdb
```

### `storage.lvm.pv.remove`

Remove LVM physical-volume metadata with an explicit confirm flag.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `confirm` | yes | `boolean` |  | Explicit destructive-operation confirmation flag. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: storage.lvm.pv.remove
with:
  device: /dev/sdb
  confirm: value
```

### `storage.lvm.pv.scan`

Refresh LVM physical-volume metadata cache.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | no | `path` |  | Block device path. |
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
use: storage.lvm.pv.scan
with:
  device: /dev/sdb
  sudo: true
```

### `storage.lvm.vg.add`

Ensure an LVM volume group exists and contains the requested PV devices.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `devices` | yes | `list` |  | Block devices to inspect. |
| `force` | no | `boolean` | `False` | Force the operation when supported. |
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
use: storage.lvm.vg.add
with:
  name: nginx
  devices:
    - /dev/sdb
```

### `storage.lvm.vg.remove`

Remove an LVM volume group with an explicit confirm flag.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `confirm` | yes | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: storage.lvm.vg.remove
with:
  name: nginx
  confirm: value
```

### `storage.lvm.vg.scan`

Scan LVM volume groups and recreate missing device nodes.

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
use: storage.lvm.vg.scan
with:
  sudo: true
```

### `storage.mount.add`

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
use: storage.mount.add
with:
  src: /dev/vdb1
  path: /data
  fstype: xfs
  opts: defaults,noatime
  persist: true
  sudo: true
```

### `storage.mount.bind`

Ensure a runtime and optional persistent bind mount.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `opts` | no | `string` | `defaults` | Mount options. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `runtime` | no | `boolean` | `True` | Apply the change to the running system. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.
- `data.path`: Bind mount target path when returned by the implementation.

Example:

```yaml
use: storage.mount.bind
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `storage.mount.check`

Check a mountpoint, source, fstype or options using findmnt.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `src` | no | `path` |  | Source path. |
| `fstype` | no | `string` |  | Filesystem type such as xfs, ext4 or nfs. |
| `opts` | no | `string` | `defaults` | Mount options. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: storage.mount.check
with:
  path: /tmp/automax-demo
```

### `storage.mount.facts`

Collect mounted filesystem facts with findmnt.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
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
use: storage.mount.facts
with:
  path: /tmp/automax-demo
  sudo: true
```

### `storage.mount.remount`

Remount an already mounted filesystem with desired options.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `opts` | no | `string` | `defaults` | Mount options. |
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
use: storage.mount.remount
with:
  path: /tmp/automax-demo
```

### `storage.mount.remove`

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
use: storage.mount.remove
with:
  path: /tmp/automax-demo
```

### `storage.multipath.add`

Add one WWID to multipath and optionally reload maps.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `wwid` | yes | `string` |  | Multipath WWID. |
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
use: storage.multipath.add
with:
  wwid: '3600508b400105e210000900000490000'
  reload: true
  sudo: true
```

### `storage.multipath.reload`

Reload multipath maps.

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
use: storage.multipath.reload
with:
  sudo: true
```

### `storage.multipath.remove`

Remove one multipath map by name or one WWID from multipath bindings.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `wwid` | no | `string` |  | Multipath WWID. |
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
use: storage.multipath.remove
with:
  name: nginx
```

### `storage.multipath.status`

Read multipath status and optionally assert a minimum path count.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | no | `string` |  | Package, user or group name. |
| `expect_paths` | no | `integer` |  | Minimum expected multipath path count. |
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
use: storage.multipath.status
with:
  name: nginx
  expect_paths: 4
```

### `storage.quota.check`

Check user or group quota limits on a mounted filesystem.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `target` | yes | `string` |  | Quota target user or group. |
| `mountpoint` | yes | `path` |  | Mounted filesystem path. |
| `type` | no | `string` | `user` | Quota subject type. |
| `block_soft` | no | `integer` | `0` | Soft block quota. |
| `block_hard` | no | `integer` | `0` | Hard block quota. |
| `inode_soft` | no | `integer` | `0` | Soft inode quota. |
| `inode_hard` | no | `integer` | `0` | Hard inode quota. |
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
use: storage.quota.check
with:
  target: value
  mountpoint: value
```

### `storage.quota.facts`

Collect user or group quota facts from a mounted filesystem.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `mountpoint` | yes | `path` |  | Mounted filesystem path. |
| `type` | no | `string` | `user` | Quota subject type. |
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
use: storage.quota.facts
with:
  mountpoint: value
```

### `storage.quota.get`

Read one user or group quota entry from a mounted filesystem.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `target` | yes | `string` |  | Quota target user or group. |
| `mountpoint` | yes | `path` |  | Mounted filesystem path. |
| `type` | no | `string` | `user` | Quota subject type. |
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
use: storage.quota.get
with:
  target: value
  mountpoint: value
```

### `storage.quota.set`

Set user or group filesystem quotas with setquota.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `target` | yes | `string` |  | Quota target user or group. |
| `mountpoint` | yes | `path` |  | Mounted filesystem path. |
| `type` | no | `string` | `user` | Quota subject type. |
| `block_soft` | no | `integer` | `0` | Soft block quota. |
| `block_hard` | no | `integer` | `0` | Hard block quota. |
| `inode_soft` | no | `integer` | `0` | Soft inode quota. |
| `inode_hard` | no | `integer` | `0` | Hard inode quota. |
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
use: storage.quota.set
with:
  type: user
  target: app
  mountpoint: /data
  block_soft: 1000000
  block_hard: 1200000
  inode_soft: 10000
  inode_hard: 12000
  sudo: true
```

### `storage.swap.add`

Ensure a swap file or swap device is active and optionally persisted in fstab.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `size` | no | `string` |  | Size such as 16G for file-backed swap. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `opts` | no | `string` | `defaults` | Mount options. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: storage.swap.add
with:
  path: /tmp/automax-demo
```

### `storage.swap.check`

Check that a swap file or device is active.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: storage.swap.check
with:
  path: /tmp/automax-demo
```

### `storage.swap.facts`

Report active swap files and devices.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: storage.swap.facts
with:
  sudo: true
```

### `storage.swap.remove`

Disable a swap file or swap device and optionally remove its fstab entry.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `persist` | no | `boolean` | `False` | Persist the change across reboots. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: storage.swap.remove
with:
  path: /tmp/automax-demo
```

### `storage.usage.disk_check`

Check remote filesystem free space and used percentage thresholds.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `min_free_mb` | no | `integer` |  | Minimum free disk space in MiB. |
| `min_free_percent` | no | `number` |  | Minimum free disk percentage. |
| `max_used_percent` | no | `number` |  | Maximum allowed used percentage. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: df output used for the disk usage check.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: storage.usage.disk_check
with:
  path: /var
  min_free_mb: 1024
  max_used_percent: 85
  sudo: true
```

### `storage.usage.inode_check`

Check remote filesystem inode free and used percentage thresholds.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `max_used_percent` | no | `number` |  | Maximum allowed used percentage. |
| `min_free_percent` | no | `number` |  | Minimum free disk percentage. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: df -i output used for the inode usage check.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: storage.usage.inode_check
with:
  path: /var
  max_used_percent: 85
  sudo: true
```

## system

### `system.cron.entry.add`

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
use: system.cron.entry.add
with:
  name: myapp-health
  schedule: '*/5 * * * *'
  user: root
  command: /usr/local/bin/myapp-healthcheck
  sudo: true
```

### `system.cron.entry.list`

List system cron.d entries and optionally one user's crontab.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | no | `string` | `False` | User account whose crontab should be listed. |
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
use: system.cron.entry.list
with:
  user: deploy
  sudo: true
```

### `system.cron.entry.remove`

Remove one /etc/cron.d entry file.

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
use: system.cron.entry.remove
with:
  name: nginx
```

### `system.cron.file`

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
use: system.cron.file
with:
  name: nginx
```

### `system.cron.validate`

Validate basic cron file syntax without installing it.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

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
use: system.cron.validate
with:
  path: /tmp/automax-demo
```

### `system.journal.collect`

Collect journalctl output for artifact capture through stdout.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `since` | no | `string` |  | Start time for journalctl queries. |
| `until` | no | `string` |  | End time for journalctl queries. |
| `lines` | no | `integer` | `200` | Number of log or journal lines to collect. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
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
use: system.journal.collect
with:
  service: sshd
  since: 1 hour ago
```

### `system.journal.grep`

Collect journalctl output and filter it with grep.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `since` | no | `string` |  | Start time for journalctl queries. |
| `until` | no | `string` |  | End time for journalctl queries. |
| `lines` | no | `integer` | `200` | Number of log or journal lines to collect. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |
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
use: system.journal.grep
with:
  pattern: KEY=.*
```

### `system.kernel.boot_param.add`

Ensure a persistent kernel boot parameter in GRUB-compatible defaults with backup and grub config regeneration.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `value` | no | `string` |  | Desired parameter value. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `update_grub` | no | `boolean` | `True` | Regenerate GRUB configuration after modifying boot parameters. |
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
use: system.kernel.boot_param.add
with:
  name: nginx
```

### `system.kernel.boot_param.remove`

Remove a kernel boot parameter from GRUB defaults after explicit confirmation.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `param` | yes | `string` |  | Kernel command-line parameter. |
| `file` | no | `path` |  | Remote configuration file path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
| `confirm` | no | `boolean` |  | Explicit destructive-operation confirmation flag. |
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
use: system.kernel.boot_param.remove
with:
  param: value
```

### `system.kernel.cmdline.check`

Assert that the running kernel command line contains or omits a parameter.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `param` | yes | `string` |  | Kernel command-line parameter. |
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
use: system.kernel.cmdline.check
with:
  param: value
```

### `system.kernel.module.blacklist`

Install or remove a persistent kernel module blacklist drop-in.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `module` | yes | `string` |  | Linux kernel module name. |
| `state` | no | `string` |  | Desired state such as present, absent, started or stopped. |
| `file` | no | `path` |  | Remote configuration file path. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: system.kernel.module.blacklist
with:
  module: br_netfilter
```

### `system.kernel.module.load`

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
use: system.kernel.module.load
with:
  name: br_netfilter
  persist: true
  sudo: true
```

### `system.kernel.module.persist`

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
use: system.kernel.module.persist
with:
  name: nginx
```

### `system.kernel.module.status`

Assert or report kernel module load status.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `module` | yes | `string` |  | Linux kernel module name. |
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
use: system.kernel.module.status
with:
  module: br_netfilter
```

### `system.kernel.module.unload`

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
use: system.kernel.module.unload
with:
  name: nginx
```

### `system.kernel.sysctl.check`

Assert a runtime sysctl value.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `value` | yes | `string` |  | Desired parameter value. |
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
use: system.kernel.sysctl.check
with:
  name: nginx
  value: 1
```

### `system.kernel.sysctl.dropin`

Install a sysctl.d drop-in and reload sysctl values.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `settings` | yes | `mapping` |  | SSH client or server settings. |
| `file` | no | `path` |  | Remote configuration file path. |
| `reload` | no | `boolean` | `False` | Reload service configuration after a change. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: system.kernel.sysctl.dropin
with:
  name: nginx
  settings: value
```

### `system.kernel.sysctl.facts`

Read one or more sysctl values.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `names` | no | `list` |  | Hostnames or aliases for a hosts entry. |
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
use: system.kernel.sysctl.facts
with:
  names:
    - app1.example.com
    - app1
  sudo: true
```

### `system.kernel.sysctl.get`

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
use: system.kernel.sysctl.get
with:
  name: nginx
```

### `system.kernel.sysctl.persist`

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
use: system.kernel.sysctl.persist
with:
  name: nginx
  value: 1
```

### `system.kernel.sysctl.reload`

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
use: system.kernel.sysctl.reload
with:
  file: /etc/sysctl.d/99-automax.conf
  sudo: true
```

### `system.kernel.sysctl.set`

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
use: system.kernel.sysctl.set
with:
  name: net.ipv4.ip_forward
  value: '1'
  runtime: true
  persist: true
  file: /etc/sysctl.d/99-automax.conf
  sudo: true
```

### `system.log.export`

Export remote log or journal output to stdout for declared artifact capture.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `files` | no | `list` |  | Target files to inspect or modify. |
| `service` | no | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
| `since` | no | `string` |  | Start time for journalctl queries. |
| `lines` | no | `integer` | `200` | Number of log or journal lines to collect. |
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
use: system.log.export
with:
  files:
    - /etc/pam.d/login
  service: sshd
```

### `system.log.grep`

Search remote log files with grep and return matching lines.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
| `files` | no | `list` |  | Target files to inspect or modify. |
| `max_count` | no | `integer` |  | Maximum number of matching log or process entries. |
| `ignore_missing` | no | `boolean` | `True` | Treat missing processes as success. |
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
use: system.log.grep
with:
  pattern: KEY=.*
```

### `system.process.check`

Check that a remote process is present or absent by PID or pattern.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pid` | no | `integer` |  | Process id. |
| `pattern` | no | `string` |  | Regex, process pattern or search pattern. |
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
use: system.process.check
with:
  pid: 1234
  pattern: KEY=.*
```

### `system.process.count_check`

Assert the number of remote processes matching a pattern.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
| `count` | no | `integer` | `0` | Maximum regex replacements; 0 means replace all matches. |
| `min_count` | no | `integer` |  | Minimum number of matching process entries. |
| `max_count` | no | `integer` |  | Maximum number of matching log or process entries. |
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
use: system.process.count_check
with:
  pattern: KEY=.*
```

### `system.process.kill`

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
use: system.process.kill
with:
  pid: 1234
  pattern: KEY=.*
```

### `system.process.signal`

Send a signal to a remote process by PID or pattern.

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
use: system.process.signal
with:
  pid: 1234
  pattern: KEY=.*
```

### `system.process.wait`

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
use: system.process.wait
with:
  pid: 1234
  pattern: KEY=.*
```

### `system.reboot`

Reboot a remote server, optionally waiting until SSH comes back.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `wait` | no | `boolean` | `False` | Wait for the operation to become reachable again when supported. |
| `delay` | no | `integer` | `3` | Initial delay in seconds. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `connect_timeout` | no | `number` | `3` | Per-attempt TCP connect timeout in seconds. |
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
use: system.reboot
with:
  wait: true
  delay: 3
```

### `system.service.active_check`

Check remote systemd active state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.active_check
with:
  service: sshd
```

### `system.service.disable`

Disable a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.disable
with:
  service: sshd
```

### `system.service.enable`

Enable a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.enable
with:
  service: sshd
```

### `system.service.enabled_check`

Check remote systemd enabled state.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.enabled_check
with:
  service: sshd
```

### `system.service.facts`

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
use: system.service.facts
with:
  sudo: true
```

### `system.service.mask`

Mask a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.mask
with:
  service: sshd
```

### `system.service.reload`

Reload a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.reload
with:
  service: sshd
```

### `system.service.restart`

Restart a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.restart
with:
  service: sshd
```

### `system.service.start`

Start a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.start
with:
  service: sshd
```

### `system.service.status`

Read remote systemd service status.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.status
with:
  service: sshd
```

### `system.service.stop`

Stop a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.stop
with:
  service: sshd
```

### `system.service.unmask`

Unmask a remote systemd service.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | yes | `string` |  | Service name, PAM service name or systemd unit depending on the plugin. |
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
use: system.service.unmask
with:
  service: sshd
```

### `system.systemd.daemon_reload`

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
use: system.systemd.daemon_reload
with:
  sudo: true
  user: deploy
```

### `system.systemd.sysusers`

Install a sysusers.d drop-in and optionally apply it immediately.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `content` | yes | `string` |  | Text content to write. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `apply` | no | `boolean` | `False` | Apply a generated system resource immediately after installation. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: system.systemd.sysusers
with:
  name: nginx
  content: managed by automax

```

### `system.systemd.timer`

Install a systemd timer file with backup, daemon-reload and optional enable/start.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `content` | yes | `string` |  | Text content to write. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `enable` | no | `boolean` | `False` | Enable a service or timer after installing its unit. |
| `start` | no | `boolean` | `False` | Start a service or timer after installing its unit. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: system.systemd.timer
with:
  name: nginx
  content: managed by automax

```

### `system.systemd.tmpfiles`

Install a tmpfiles.d drop-in and optionally apply it immediately.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `content` | yes | `string` |  | Text content to write. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `apply` | no | `boolean` | `False` | Apply a generated system resource immediately after installation. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: system.systemd.tmpfiles
with:
  name: nginx
  content: managed by automax

```

### `system.systemd.unit`

Install a systemd unit file with backup, daemon-reload and optional enable/start.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `name` | yes | `string` |  | Package, user or group name. |
| `content` | yes | `string` |  | Text content to write. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `enable` | no | `boolean` | `False` | Enable a service or timer after installing its unit. |
| `start` | no | `boolean` | `False` | Start a service or timer after installing its unit. |
| `backup` | no | `boolean` | `False` | Create a backup before modifying an existing file. |
| `backup_suffix` | no | `string` | `.bak` | Suffix appended to the original path when backup is enabled. |
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
use: system.systemd.unit
with:
  name: nginx
  content: managed by automax

```
