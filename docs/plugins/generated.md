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

## alternatives

### `alternatives.get`

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
use: alternatives.get
with:
  name: nginx
```

### `alternatives.list`

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
use: alternatives.list
with:
  sudo: true
```

### `alternatives.set`

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
use: alternatives.set
with:
  name: nginx
  path: /tmp/automax-demo
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

## auditd

### `auditd.reload`

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
use: auditd.reload
with:
  sudo: true
```

### `auditd.rule`

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
use: auditd.rule
with:
  name: nginx
```

### `auditd.status`

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
use: auditd.status
with:
  sudo: true
```

## authselect

### `authselect.profile`

Select an authselect profile with optional features and backup.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `profile` | yes | `string` |  | AppArmor profile name or profile file path. |
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
use: authselect.profile
with:
  profile: /etc/apparmor.d/usr.sbin.nginx
```

## backup

### `backup.directory`

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
use: backup.directory
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `backup.file`

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
use: backup.file
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `backup.restore`

Restore a remote file or tar archive from an explicit backup artifact.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `confirm` | yes | `boolean` |  | Explicit destructive-operation confirmation flag. |
| `archive` | no | `path` |  | Remote archive path to extract. |
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
use: backup.restore
with:
  src: /tmp/source
  dest: /tmp/dest
  confirm: value
```

### `backup.verify`

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
use: backup.verify
with:
  path: /tmp/automax-demo
```

## blkid

### `blkid.assert`

Assert block-device identity fields reported by blkid.

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
use: blkid.assert
with:
  device: /dev/sdb
```

## block

### `block.facts`

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
use: block.facts
with:
  devices:
    - /dev/sdb
  multipath: false
```

### `block.identity`

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
use: block.identity
with:
  device: /dev/sdb
```

### `block.mkfs`

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
use: block.mkfs
with:
  device: /dev/sdb
  fstype: xfs
```

### `block.partition`

Conservatively create a partition table and missing partitions with parted.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `device` | yes | `path` |  | Block device path. |
| `label` | yes | `string` |  | Disk label, filesystem label or partition label. |
| `partitions` | yes | `list` |  | Desired partition entries for a block.partition operation. |
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
use: block.partition
with:
  device: /dev/sdb
  label: gpt
  partitions:
    - {'number': 1, 'name': 'DATA01', 'start': '1MiB', 'end': '100%'}
```

### `block.partition_rescan`

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
use: block.partition_rescan
with:
  device: /dev/sdb
```

### `block.rescan`

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
use: block.rescan
with:
  device: /dev/sdb
  udev_settle: true
```

### `block.wipe_signatures`

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
use: block.wipe_signatures
with:
  device: /dev/sdb
```

## cert

### `cert.expiry_report`

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
use: cert.expiry_report
with:
  cert: value
```

### `cert.fingerprint`

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
use: cert.fingerprint
with:
  cert: value
```

### `cert.generate_csr`

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
use: cert.generate_csr
with:
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
  dest: /tmp/dest
  subject: Automax notification
```

### `cert.install_ca_bundle`

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
use: cert.install_ca_bundle
with:
  src: /tmp/source
  dest: /tmp/dest
```

### `cert.install_keypair`

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
use: cert.install_keypair
with:
  cert: value
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
  cert_dest: value
  key_dest: value
```

### `cert.issuer_assert`

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
use: cert.issuer_assert
with:
  cert: value
  issuer: CN=Example CA
```

### `cert.matches_key`

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
use: cert.matches_key
with:
  cert: value
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
```

### `cert.san_assert`

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
use: cert.san_assert
with:
  cert: value
  names:
    - app1.example.com
    - app1
```

### `cert.self_signed`

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
use: cert.self_signed
with:
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
  cert: value
  subject: Automax notification
```

### `cert.subject_assert`

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
use: cert.subject_assert
with:
  cert: value
  subject: Automax notification
```

### `cert.verify_chain`

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
use: cert.verify_chain
with:
  cert: value
  ca_file: value
```

## chrony

### `chrony.servers`

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
use: chrony.servers
with:
  servers:
    - time.example.com
```

### `chrony.sources_assert`

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
use: chrony.sources_assert
with:
  sudo: true
```

## cron

### `cron.absent`

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
use: cron.absent
with:
  name: nginx
```

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

### `cron.list`

List system cron.d entries and optionally one user's crontab.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
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
use: cron.list
with:
  user: false
  sudo: true
```

### `cron.validate`

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
use: cron.validate
with:
  path: /tmp/automax-demo
```

## db

### `db.health`

Run read-only controller-side database health checks.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `engine` | yes | `string` |  | Database engine such as sqlite, postgres, mysql or oracle. |
| `connection` | no | `mapping` |  | Database connection mapping; values may be rendered from vars or secrets. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `checks` | no | `list` |  | Health checks to run. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `output` | no | `string` | `rows` | Database output format: rows, scalar, json or none. |

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
use: db.health
with:
  engine: value
```

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

## download

### `download.file`

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
use: download.file
with:
  url: https://example.invalid/health
  dest: /tmp/dest
```

## env

### `env.set`

Set step-scoped or persistent shell environment variables.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `variables` | yes | `mapping` |  | Environment variables to set. |
| `scope` | no | `string` | `step` | Environment scope: step, user, global or file. |
| `path` | no | `path` |  | Remote or local path, depending on the plugin. |
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |
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
use: env.set
with:
  variables:
    APP_HOME: /opt/app
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

## findmnt

### `findmnt.assert`

Assert a mountpoint, source, fstype or options using findmnt.

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
use: findmnt.assert
with:
  path: /tmp/automax-demo
```

## firewalld

### `firewalld.list`

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
use: firewalld.list
with:
  zone: public
  permanent: true
```

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

### `firewalld.status`

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
use: firewalld.status
with:
  sudo: true
```

### `firewalld.zone`

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
use: firewalld.zone
with:
  zone: public
```

## fs

### `fs.acl`

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
use: fs.acl
with:
  path: /tmp/automax-demo
  acl: value
```

### `fs.attr`

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
use: fs.attr
with:
  path: /tmp/automax-demo
  attrs: value
```

### `fs.bind_mount`

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
use: fs.bind_mount
with:
  src: /tmp/source
  dest: /tmp/dest
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

### `fs.disk_usage_assert`

Assert that filesystem block usage is below a maximum percentage.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `max_percent` | yes | `integer` |  | Maximum allowed percentage. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: df assertion output.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.disk_usage_assert
with:
  path: /tmp/automax-demo
  max_percent: value
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

### `fs.inode_usage_assert`

Assert that filesystem inode usage is below a maximum percentage.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `path` | yes | `path` |  | Remote or local path, depending on the plugin. |
| `max_percent` | yes | `integer` |  | Maximum allowed percentage. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: df -i assertion output.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: fs.inode_usage_assert
with:
  path: /tmp/automax-demo
  max_percent: value
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

### `fs.quota`

Set user or group filesystem quotas with setquota.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `target` | yes | `string` |  | Quota target user or group. |
| `mountpoint` | yes | `path` |  | Mounted filesystem path. |
| `type` | no | `string` |  | Path type filter: path, file, directory, dir, symlink or any. |
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
use: fs.quota
with:
  target: value
  mountpoint: value
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

### `fs.resize`

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
use: fs.resize
with:
  device: /dev/sdb
  fstype: xfs
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

### `fstab.validate`

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
use: fstab.validate
with:
  file: /etc/sysctl.d/99-automax.conf
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

## health

### `health.http`

Assert HTTP status and optional body content from the controller.

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

Example:

```yaml
use: health.http
with:
  url: https://example.invalid/health
```

### `health.listen`

Assert that a TCP port is listening on the target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `port` | yes | `integer` |  | TCP port number. |
| `host` | no | `string` |  | Hostname or IP address to check from the controller. |
| `listen` | no | `boolean` | `True` | Check whether a port is listening on the target. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: health.listen
with:
  port: 22
```

### `health.port`

Assert that a TCP port is reachable from the controller or listening on the target.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `port` | yes | `integer` |  | TCP port number. |
| `host` | no | `string` |  | Hostname or IP address to check from the controller. |
| `listen` | no | `boolean` | `True` | Check whether a port is listening on the target. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: health.port
with:
  port: 22
```

### `health.process`

Assert that a remote process matching a pattern exists or is absent.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
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
use: health.process
with:
  pattern: KEY=.*
```

## hostname

### `hostname.set`

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
use: hostname.set
with:
  name: nginx
```

## hosts

### `hosts.entry`

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
use: hosts.entry
with:
  ip: 192.0.2.10
  names:
    - app1.example.com
    - app1
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

## iptables

### `iptables.chain`

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
use: iptables.chain
with:
  chain: value
```

### `iptables.list`

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
use: iptables.list
with:
  table: main
```

### `iptables.policy`

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
use: iptables.policy
with:
  chain: value
```

### `iptables.restore`

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
use: iptables.restore
with:
  src: /tmp/source
```

### `iptables.rule`

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
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: iptables.rule
with:
  chain: value
  rule: allow
```

### `iptables.save`

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
use: iptables.save
with:
  dest: /tmp/dest
```

## journal

### `journal.collect`

Collect journalctl output for artifact capture through stdout.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `service` | no | `string` |  | systemd service unit name. |
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
use: journal.collect
with:
  service: sshd
  since: 1 hour ago
```

### `journal.grep`

Collect journalctl output and filter it with grep.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
| `service` | no | `string` |  | systemd service unit name. |
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
use: journal.grep
with:
  pattern: KEY=.*
```

## kernel

### `kernel.boot_param`

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
use: kernel.boot_param
with:
  name: nginx
```

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

## limits

### `limits.dropin`

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
use: limits.dropin
with:
  name: nginx
  entries:
    - {'domain': 'appuser', 'type': 'soft', 'item': 'nofile', 'value': 1024}
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

## log

### `log.export`

Export remote log or journal output to stdout for declared artifact capture.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `files` | no | `list` |  | Target files to inspect or modify. |
| `service` | no | `string` |  | systemd service unit name. |
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
use: log.export
with:
  files:
    - /etc/pam.d/login
  service: sshd
```

### `log.grep`

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
use: log.grep
with:
  pattern: KEY=.*
```

## login

### `login.defs`

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
use: login.defs
with:
  settings: value
```

## lvm

### `lvm.facts`

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
use: lvm.facts
with:
  vg: vg_app
  name: nginx
```

### `lvm.lv_assert`

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
use: lvm.lv_assert
with:
  vg: vg_app
  name: nginx
```

### `lvm.lv_extend`

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
use: lvm.lv_extend
with:
  vg: vg_app
  name: nginx
  size: 16G
```

### `lvm.lv_present`

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
use: lvm.lv_present
with:
  vg: vg_app
  name: nginx
  size: 16G
```

### `lvm.lv_remove`

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
use: lvm.lv_remove
with:
  path: /tmp/automax-demo
  confirm: value
```

### `lvm.pv_present`

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
use: lvm.pv_present
with:
  device: /dev/sdb
```

### `lvm.pv_remove`

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
use: lvm.pv_remove
with:
  device: /dev/sdb
  confirm: value
```

### `lvm.resizefs`

Resize a filesystem after a block or LVM volume change.

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
use: lvm.resizefs
with:
  device: /dev/sdb
  fstype: xfs
```

### `lvm.snapshot`

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
use: lvm.snapshot
with:
  vg: vg_app
  source: /var/log/app
  name: nginx
  size: 16G
```

### `lvm.thin_pool`

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
use: lvm.thin_pool
with:
  vg: vg_app
  name: nginx
  size: 16G
```

### `lvm.vg_present`

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
use: lvm.vg_present
with:
  name: nginx
  devices:
    - /dev/sdb
```

### `lvm.vg_remove`

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
use: lvm.vg_remove
with:
  name: nginx
  confirm: value
```

## mail

### `mail.send`

Send an email from the Automax controller through SMTP.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `smtp_host` | yes | `string` |  | SMTP server host used by the Automax controller. |
| `from` | yes | `string` |  | Source address for firewall rules. |
| `to` | yes | `string` |  | Destination address for firewall rules. |
| `subject` | yes | `string` |  | Email subject line. |
| `smtp_port` | no | `integer` | `587` | SMTP server port. |
| `starttls` | no | `boolean` | `True` | Use STARTTLS before SMTP authentication. |
| `ssl` | no | `boolean` | `False` | Use implicit TLS for SMTP. |
| `username` | no | `string` |  | SMTP username; prefer values rendered from secrets. |
| `password` | no | `string` |  | Plaintext password; prefer password_hash when possible. |
| `body` | no | `string` |  | Raw HTTP request body. |
| `cc` | no | `list` |  | Email CC recipients. |
| `bcc` | no | `list` |  | Email BCC recipients. |
| `reply_to` | no | `string` |  | Email Reply-To address. |
| `attachments` | no | `list` |  | Local controller-side attachment paths. |
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
use: mail.send
with:
  smtp_host: smtp.example.com
  from: 10.0.0.0/8
  to: any
  subject: Automax notification
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

### `mount.facts`

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
use: mount.facts
with:
  path: /tmp/automax-demo
  sudo: true
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

### `mount.remount`

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
use: mount.remount
with:
  path: /tmp/automax-demo
```

## multipath

### `multipath.flush`

Flush one multipath map.

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
use: multipath.flush
with:
  name: nginx
```

### `multipath.reload`

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
use: multipath.reload
with:
  sudo: true
```

### `multipath.status`

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
use: multipath.status
with:
  name: nginx
  expect_paths: 4
```

## network

### `network.bond`

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
use: network.bond
with:
  name: nginx
  interfaces:
    - eth1
    - eth2
```

### `network.bridge`

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
use: network.bridge
with:
  name: nginx
```

### `network.dns`

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
use: network.dns
with:
  backend: auto
  nameservers:
    - 192.0.2.53
```

### `network.dns_assert`

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
use: network.dns_assert
with:
  nameservers:
    - 192.0.2.53
  search:
    - example.com
```

### `network.interface`

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
use: network.interface
with:
  name: nginx
```

### `network.link_assert`

Assert that a network link exists and optionally has expected state or MTU.

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
use: network.link_assert
with:
  name: nginx
```

### `network.port_check`

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

Example:

```yaml
use: network.port_check
with:
  host: 127.0.0.1
  port: 22
```

### `network.route`

Ensure a runtime and optional persistent IP route is present or absent.

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
use: network.route
with:
  dest: /tmp/dest
```

### `network.route_assert`

Assert that a route exists with optional gateway, device, table or metric.

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
use: network.route_assert
with:
  dest: /tmp/dest
```

### `network.vlan`

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
use: network.vlan
with:
  name: nginx
  parent: eth0
  vlan_id: 100
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

### `nftables.export`

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
use: nftables.export
with:
  family: inet
  table: main
```

### `nftables.list`

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
use: nftables.list
with:
  family: inet
  table: main
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

## pam

### `pam.limits`

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
use: pam.limits
with:
  files:
    - /etc/pam.d/login
```

## password

### `password.policy`

Install a pwquality password policy drop-in.

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
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: password.policy
with:
  name: nginx
  settings: value
```

## pkg

### `pkg.clean`

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
use: pkg.clean
with:
  manager: auto
  sudo: true
```

### `pkg.files`

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
use: pkg.files
with:
  name: nginx
```

### `pkg.hold`

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
use: pkg.hold
with:
  name: nginx
  packages:
    - curl
```

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

### `pkg.owner`

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
use: pkg.owner
with:
  path: /tmp/automax-demo
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

### `pkg.repo_priority`

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
use: pkg.repo_priority
with:
  name: nginx
  priority: 1001
```

### `pkg.unhold`

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
use: pkg.unhold
with:
  name: nginx
  packages:
    - curl
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

### `pkg.verify`

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
use: pkg.verify
with:
  name: nginx
  packages:
    - curl
```

### `pkg.version_assert`

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
use: pkg.version_assert
with:
  name: nginx
  version: 1.2.3*
```

### `pkg.version_pin`

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
use: pkg.version_pin
with:
  name: nginx
  version: 1.2.3*
```

## pki

### `pki.ca_install`

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
use: pki.ca_install
with:
  dest: /tmp/dest
  name: nginx
```

### `pki.cert_expiry_assert`

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
use: pki.cert_expiry_assert
with:
  path: /tmp/automax-demo
```

### `pki.key_permissions`

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
use: pki.key_permissions
with:
  path: /tmp/automax-demo
```

## platform

### `platform.facts`

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
use: platform.facts
with:
  sudo: true
```

## process

### `process.assert_absent`

Assert that no remote process matches a pattern.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `pattern` | yes | `string` |  | Regex, process pattern or search pattern. |
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: process.assert_absent
with:
  pattern: KEY=.*
```

### `process.assert_count`

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
use: process.assert_count
with:
  pattern: KEY=.*
```

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

### `process.signal`

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
use: process.signal
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

## resolver

### `resolver.config`

Manage DNS resolver settings safely using explicit plain-file, systemd-resolved, NetworkManager or resolvconf backends.

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
use: resolver.config
with:
  backend: auto
  nameservers:
    - 192.0.2.53
```

### `resolver.facts`

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
use: resolver.facts
with:
  sudo: true
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

### `selinux.fcontext`

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
use: selinux.fcontext
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

### `selinux.port`

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
use: selinux.port
with:
  port: 22
  protocol: tcp
  selinux_type: httpd_sys_content_t
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

### `ssh.authorized_key_absent`

Remove one SSH authorized_keys line for a remote user.

- Remote session: `true`
- Dry-run support: `true`
- Check mode support: `false`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `user` | yes | `boolean` | `False` | Use systemctl --user instead of the system manager. |
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
use: ssh.authorized_key_absent
with:
  user: false
  key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example
```

### `ssh.config`

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
use: ssh.config
with:
  name: nginx
  settings: value
```

### `ssh.fingerprint`

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
use: ssh.fingerprint
with:
  path: /tmp/automax-demo
```

### `ssh.host_keygen`

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
use: ssh.host_keygen
with:
  types:
    - ed25519
  force: true
```

### `ssh.keygen`

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
use: ssh.keygen
with:
  path: /tmp/automax-demo
```

### `ssh.known_hosts`

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
| `user` | no | `boolean` | `False` | Use systemctl --user instead of the system manager. |
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
use: ssh.known_hosts
with:
  host: 127.0.0.1
```

### `ssh.public_key`

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
use: ssh.public_key
with:
  path: /tmp/automax-demo
```

## sshd

### `sshd.config`

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
| `sudo` | no | `boolean` | `False` | Run the remote operation through sudo -n when supported. |

Result fields:

- `changed`: Whether the plugin changed the target or controller state.
- `message`: Human-readable result message.
- `rc`: Process or command return code when applicable.
- `stdout`: Captured standard output when applicable.
- `stderr`: Captured standard error when applicable.
- `data`: Plugin-specific structured result data.

Example:

```yaml
use: sshd.config
with:
  name: nginx
  settings: value
```

### `sshd.validate`

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
use: sshd.validate
with:
  sudo: true
```

## sudo

### `sudo.rule`

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
use: sudo.rule
with:
  name: nginx
  subject: Automax notification
```

### `sudo.validate`

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
use: sudo.validate
with:
  path: /tmp/automax-demo
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

## swap

### `swap.absent`

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
use: swap.absent
with:
  path: /tmp/automax-demo
```

### `swap.present`

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
use: swap.present
with:
  path: /tmp/automax-demo
```

### `swap.status`

Report active swap devices and optionally assert one path is active.

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
use: swap.status
with:
  path: /tmp/automax-demo
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

## system

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

## systemd

### `systemd.sysusers`

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
use: systemd.sysusers
with:
  name: nginx
  content: managed by automax

```

### `systemd.timer`

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
use: systemd.timer
with:
  name: nginx
  content: managed by automax

```

### `systemd.tmpfiles`

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
use: systemd.tmpfiles
with:
  name: nginx
  content: managed by automax

```

### `systemd.unit`

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
use: systemd.unit
with:
  name: nginx
  content: managed by automax

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

### `transfer.rsync`

Synchronize files with rsync using the current target as the default remote endpoint.

- Remote session: `false`
- Dry-run support: `true`
- Check mode support: `true`

| Parameter | Required | Type | Default | Description |
|---|---:|---|---|---|
| `src` | yes | `path` |  | Source path. |
| `dest` | yes | `path` |  | Destination path. |
| `direction` | no | `string` | `upload` | Transfer direction such as upload, download or local. |
| `archive` | no | `path` |  | Remote archive path to extract. |
| `compress` | no | `boolean` | `False` | Enable stream compression when supported. |
| `delete` | no | `boolean` | `False` | Delete extraneous destination files when supported. |
| `checksum` | no | `string` |  | Expected SHA256 checksum for a downloaded file. |
| `dry_run` | no | `boolean` | `False` | Render or run without applying changes when supported. |
| `excludes` | no | `list` |  | Glob patterns excluded from archive creation. |
| `ssh_options` | no | `list` |  | Extra ssh options used by rsync. |
| `rsync_path` | no | `path` |  | Remote rsync executable path. |
| `timeout` | no | `number` |  | Operation timeout in seconds. |

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
use: transfer.rsync
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

## udev

### `udev.reload`

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
use: udev.reload
with:
  sudo: true
```

### `udev.rule`

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
use: udev.rule
with:
  path: /tmp/automax-demo
```

### `udev.settle`

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
use: udev.settle
with:
  timeout: 60
```

### `udev.trigger`

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
use: udev.trigger
with:
  subsystem: block
  action: change
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
