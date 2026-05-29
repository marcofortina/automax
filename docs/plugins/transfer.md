<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Transfer plugins

Transfer plugins move files between the controller and the remote target over the
active SSH connection.

## `data.transfer.upload`

Uploads a local file or directory to the remote target. Directory upload requires `recursive: true`. `sudo: true` is supported for file uploads only because the file is uploaded to a temporary path and then installed with elevated privileges.

```yaml
- id: upload_release
  use: data.transfer.upload
  with:
    src: ./dist/myapp.tar.gz
    dest: /tmp/myapp.tar.gz
```

For small local directory trees, use `data.transfer.upload` with `recursive: true`. This uses the active SSH/SFTP connection and does not delete remote files that are missing locally. For large or incremental directory trees, use `data.transfer.rsync`.

## `data.transfer.download`

Downloads a remote file or directory to the controller. Directory download requires `recursive: true`.

```yaml
- id: collect_log
  use: data.transfer.download
  with:
    src: /var/log/myapp/app.log
    dest: ./artifacts/{{ server.name }}/app.log
```

## Rsync transfers

`data.transfer.rsync` uses the controller-side `rsync` executable and the current
Automax target as the default remote endpoint. It is intended for large or
incremental transfers where SFTP upload/download would be too slow.

Example:

```yaml
use: data.transfer.rsync
with:
  src: ./dist/
  dest: /opt/app/
  delete: true
  dry_run: true
```

The preview path is rsync-native: use `dry_run: true` or job dry-run mode to
render a copy/pasteable `rsync --dry-run` command before applying changes.

## Transfer safeguards

`data.transfer.upload` and `data.transfer.download` support checksum validation,
`overwrite`, `backup_existing`, `backup_suffix`, timestamp preservation and file
mode handling. Directory uploads can also receive recursive owner/group/mode
application after transfer.

## Rsync operational controls

`data.transfer.rsync` supports partial transfers, bandwidth limiting, numeric ids,
itemized change output and transfer statistics in addition to existing checksum,
compress, delete and dry-run controls.
