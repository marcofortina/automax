# Archive plugins

Archive plugins operate on remote paths through SSH and use standard remote
commands: `tar`, `zip` and `unzip`.

## `archive.tar`

Creates a tar archive from a remote source path.

```yaml
- id: pack_logs
  use: archive.tar
  with:
    source: /var/log/myapp
    dest: /tmp/myapp-logs.tar.gz
    compression: gzip
    excludes:
      - "*.tmp"
      - "*.lock"
    creates: /tmp/myapp-logs.tar.gz
```

`compression` can be `none`, `gzip`, `bzip2` or `xz`.

## `archive.untar`

Extracts a tar archive on the remote target.

```yaml
- id: unpack_release
  use: archive.untar
  with:
    archive: /tmp/myapp.tar.gz
    dest: /opt/myapp/releases/{{ run_id | default('manual') }}
    strip_components: 1
    creates: /opt/myapp/releases/current/bin/myapp
    sudo: true
```

## `archive.zip`

Creates a zip archive from a remote source path.

```yaml
- id: zip_report
  use: archive.zip
  with:
    source: /tmp/report
    dest: /tmp/report.zip
    excludes:
      - "*.bak"
```

## `archive.unzip`

Extracts a zip archive on the remote target.

```yaml
- id: unzip_package
  use: archive.unzip
  with:
    archive: /tmp/package.zip
    dest: /opt/package
    overwrite: false
    creates: /opt/package/bin/app
```
