<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Archive plugins

Archive plugins operate on remote paths through SSH and use standard remote
commands: `tar`, `gzip`, `bzip2`, `xz`, `zip` and `unzip`.

## `data.archive.tar.create`

Creates a tar archive from a remote source path.

```yaml
- id: pack_logs
  use: data.archive.tar.create
  with:
    source: /var/log/myapp
    dest: /tmp/myapp-logs.tar.gz
    compression: gzip
    excludes:
      - "*.tmp"
      - "*.lock"
    creates: /tmp/myapp-logs.tar.gz
```

`compression` can be `auto`, `none`, `gzip`, `bzip2` or `xz`. `auto` is the default and derives the tar mode from the archive suffix when possible.

## `data.archive.tar.extract`

Extracts a tar archive on the remote target.

```yaml
- id: unpack_release
  use: data.archive.tar.extract
  with:
    archive: /tmp/myapp.tar.gz
    dest: /opt/myapp/releases/{{ vars.release_id }}
    strip_components: 1
    creates: /opt/myapp/releases/{{ vars.release_id }}/bin/myapp
```

## `data.compression.gzip.compress`

Compresses one remote file to a standalone gzip, bzip2 or xz file. Tar archive
compression such as `.tar.gz` remains handled by `data.archive.tar.create`; use this plugin
for single-file `.gz`, `.bz2` or `.xz` outputs.

```yaml
- id: compress_report
  use: data.compression.gzip.compress
  with:
    source: /tmp/report.log
    dest: /tmp/report.log.gz
    compression: auto
```

## `data.compression.gzip.decompress`

Decompresses one standalone gzip, bzip2 or xz file to a remote destination file.

```yaml
- id: decompress_report
  use: data.compression.gzip.decompress
  with:
    archive: /tmp/report.log.bz2
    dest: /tmp/report.log
    compression: auto
```

## `data.archive.zip.create`

Creates a zip archive from a remote source path.

```yaml
- id: zip_report
  use: data.archive.zip.create
  with:
    source: /tmp/report
    dest: /tmp/report.zip
    excludes:
      - "*.bak"
```

## `data.archive.zip.extract`

Extracts a zip archive on the remote target.

```yaml
- id: unzip_package
  use: data.archive.zip.extract
  with:
    archive: /tmp/package.zip
    dest: /opt/package
    overwrite: false
    creates: /opt/package/bin/app
```


Archive plugins do not add `sudo` themselves. Run them as a user with the required remote permissions, or wrap exceptional privileged archive operations with an explicit `command.remote.run` until privileged archive support is added.

## Safe extraction

`data.archive.tar.extract` and `data.archive.zip.extract` support checksum verification and safe
extraction checks that reject absolute paths or `..` traversal before extracting.
They also support include/exclude filtering and post-extract owner/group/mode
handling.
