<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Filesystem plugins

Filesystem plugins operate on the current remote target through SSH unless noted
otherwise. They are designed to be explicit and idempotent where possible.

## `fs.exists`

Checks whether a path exists and returns `data.exists` without failing when it is
missing.

```yaml
- id: check_config
  use: fs.exists
  with:
    path: /etc/myapp/app.conf
    type: file
  register:
    config_exists: data.exists
```

`type` can be `file`, `directory`, `dir`, `path`, `any`.

## `fs.stat`

Returns metadata for a remote path.

```yaml
- id: stat_binary
  use: fs.stat
  with:
    path: /usr/local/bin/myapp
  register:
    binary_size: data.size
```

Returned data includes `exists`, `type`, `size`, `mode`, `owner`, `group`, `mtime`
and `path`.

## `fs.read`

Reads a remote text file.

```yaml
- id: read_version
  use: fs.read
  with:
    path: /opt/myapp/VERSION
  register:
    version_file: data.content
```

## `fs.write`

Writes text content to a remote file. The plugin uploads to a temporary file and
installs only when content differs.

```yaml
- id: write_env
  use: fs.write
  with:
    path: /etc/myapp/env
    content: |
      APP_ENV={{ vars.environment }}
      APP_VERSION={{ vars.version }}
    owner: root
    group: root
    mode: "0644"
    sudo: true
```

## `fs.template`

Renders a local Jinja2 template and writes it to the remote target.

```yaml
- id: render_config
  use: fs.template
  with:
    src: ./templates/app.conf.j2
    dest: /etc/myapp/app.conf
    owner: root
    group: root
    mode: "0644"
    sudo: true
    values:
      listen_port: 8080
```

Templates can use `job`, `task`, `step`, `substep`, `server`, `target`, `vars`,
`secrets`, `outputs`, `step_state` and `values`.

## `fs.line`

Ensures one exact line is present or absent.

```yaml
- id: enable_setting
  use: fs.line
  with:
    path: /etc/myapp/app.conf
    line: "feature_enabled=true"
    state: present
    create: true
    sudo: true
```

## `fs.replace`

Replaces text with a Python regular expression. Use `backup: true` when you
want Automax to copy the pre-change file before writing replacements. By
default the backup path is the original path plus `.bak`; use `backup_suffix` or
`backup_path` to customize it.

```yaml
- id: update_port
  use: fs.replace
  with:
    path: /etc/myapp/app.conf
    pattern: "^port=.*$"
    replacement: "port=8080"
    backup: true
    backup_suffix: ".pre-automax"
    sudo: true
```

## `fs.mkdir`

Ensures a directory exists.

```yaml
- id: create_app_dir
  use: fs.mkdir
  with:
    path: /opt/myapp
    owner: myapp
    group: myapp
    mode: "0755"
    sudo: true
```

## `fs.copy`

Copies a remote source path to a remote destination path.

```yaml
- id: copy_config_backup
  use: fs.copy
  with:
    src: /etc/myapp/app.conf
    dest: /etc/myapp/app.conf.bak
    overwrite: false
    sudo: true
```

## `fs.move`

Moves or renames a remote path.

```yaml
- id: activate_file
  use: fs.move
  with:
    src: /tmp/myapp.conf
    dest: /etc/myapp/app.conf
    sudo: true
```

## `fs.symlink.create`

Creates a symbolic link or updates an existing symlink to point at the requested source.

The default behavior is conservative: Automax refuses to replace an existing symlink
that points somewhere else unless `force: true` is set, and it refuses to replace a
regular file or directory unless both `force: true` and
`allow_replace_non_symlink: true` are set. This avoids accidentally deleting real
paths when a link path is wrong.

```yaml
- id: switch_current
  use: fs.symlink.create
  with:
    src: /opt/myapp/releases/2026-05-22
    dest: /opt/myapp/current
    force: true
    sudo: true
```

To intentionally replace a non-symlink path, be explicit:

```yaml
- id: replace_wrong_current_path
  use: fs.symlink.create
  with:
    src: /opt/myapp/releases/2026-05-22
    dest: /opt/myapp/current
    force: true
    allow_replace_non_symlink: true
    sudo: true
```

## `fs.symlink.remove`

Removes a symbolic link without deleting regular files or directories. Missing
links are treated as already absent. If the path exists but is not a symlink, the
plugin fails.

```yaml
- id: remove_current_link
  use: fs.symlink.remove
  with:
    path: /opt/myapp/current
    sudo: true
```

## `fs.find`

Finds paths under a root path.

```yaml
- id: find_logs
  use: fs.find
  with:
    path: /var/log/myapp
    name: "*.log"
    type: file
  register:
    log_files: data.paths
```

## `fs.chown` and `fs.chmod`

Manage ownership and permissions.

```yaml
- id: fix_owner
  use: fs.chown
  with:
    path: /opt/myapp
    owner: myapp
    group: myapp
    recursive: true
    sudo: true

- id: fix_mode
  use: fs.chmod
  with:
    path: /opt/myapp/bin/myapp
    mode: "0755"
    sudo: true
```

## `fs.cd`

Sets the step-local working directory used by later remote plugins in the same
step.

```yaml
- id: enter_release_dir
  use: fs.cd
  with:
    path: /opt/myapp/current

- id: run_from_current
  use: remote.command
  with:
    command: "./bin/myapp --version"
```

`fs.cd` does not keep a shell open. It updates Automax `step_state` and later
remote commands are prefixed with `cd <path> &&` where supported.


## Operational backups

`backup.file` creates an explicit remote backup copy and checksum before risky
maintenance operations. Backup operations are intentionally separate from file
mutation plugins so operators can preview and run them as dedicated steps.
