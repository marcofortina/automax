<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Filesystem plugins

Filesystem plugins operate on the current remote target through SSH unless noted
otherwise. They are designed to be explicit and idempotent where possible.

## Type-strict path families

Automax exposes type-specific filesystem resources instead of a generic path
operation. Directory and regular-file checks explicitly reject symlinks, even
when the symlink target has the requested type. Symlink checks match symlinks
only, including broken symlinks.

```text
fs.dir.create      # create a real directory
fs.dir.remove      # remove a real directory; recursive=true removes non-empty trees
fs.dir.check      # report whether a real directory exists; fail on wrong type
fs.dir.wait        # wait for a real directory to be present or absent

fs.file.create     # create a real regular file
fs.file.remove     # remove a real regular file; fail on directories/symlinks
fs.file.check     # report whether a real regular file exists; fail on wrong type
fs.file.wait       # wait for a real regular file to be present or absent

fs.symlink.create  # create or update a symlink
fs.symlink.remove  # remove a symlink; fail on files/directories
fs.symlink.check  # report whether a symlink exists; fail on wrong type
fs.symlink.wait    # wait for a symlink to be present or absent
```

`*.exists` returns `data.exists: false` when the path is absent. It fails only
when the path exists with a different type. `*.wait` uses `retries` and
`interval`, not a timeout.

```yaml
- id: create_app_dir
  use: fs.dir.create
  with:
    path: /opt/myapp
    owner: myapp
    group: myapp
    mode: "0755"
    sudo: true

- id: wait_for_config
  use: fs.file.wait
  with:
    path: /etc/myapp/app.conf
    state: present
    retries: 12
    interval: 5

- id: remove_empty_dir
  use: fs.dir.remove
  with:
    path: /opt/myapp/old-empty-dir

- id: remove_tree
  use: fs.dir.remove
  with:
    path: /opt/myapp/old-release
    recursive: true
```

## `fs.path.stat`

Returns metadata for a remote path.

```yaml
- id: stat_binary
  use: fs.path.stat
  with:
    path: /usr/local/bin/myapp
  register:
    binary_size: data.size
```

Returned data includes `exists`, `type`, `size`, `mode`, `owner`, `group`, `mtime`
and `path`.

## `fs.file.read`

Reads a remote text file.

```yaml
- id: read_version
  use: fs.file.read
  with:
    path: /opt/myapp/VERSION
  register:
    version_file: data.content
```

## `fs.file.write`

Writes text content to a remote file. The plugin uploads to a temporary file and
installs only when content differs.

```yaml
- id: write_env
  use: fs.file.write
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

## `fs.file.template`

Renders a local Jinja2 template and writes it to the remote target.

```yaml
- id: render_config
  use: fs.file.template
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

## `fs.file.line`

Ensures one exact line is present or absent.

```yaml
- id: enable_setting
  use: fs.file.line
  with:
    path: /etc/myapp/app.conf
    line: "feature_enabled=true"
    state: present
    create: true
    sudo: true
```

## `fs.file.replace`

Replaces text with a Python regular expression. Use `backup: true` when you
want Automax to copy the pre-change file before writing replacements. By
default the backup path is the original path plus `.bak`; use `backup_suffix` or
`backup_path` to customize it.

```yaml
- id: update_port
  use: fs.file.replace
  with:
    path: /etc/myapp/app.conf
    pattern: "^port=.*$"
    replacement: "port=8080"
    backup: true
    backup_suffix: ".pre-automax"
    sudo: true
```

## `fs.path.copy`

Copies a remote source path to a remote destination path.

```yaml
- id: copy_config_backup
  use: fs.path.copy
  with:
    src: /etc/myapp/app.conf
    dest: /etc/myapp/app.conf.bak
    overwrite: false
    sudo: true
```

## `fs.path.move`

Moves or renames a remote path.

```yaml
- id: activate_file
  use: fs.path.move
  with:
    src: /tmp/myapp.conf
    dest: /etc/myapp/app.conf
    sudo: true
```

## `fs.symlink.create` / `fs.symlink.remove`

`fs.symlink.create` creates a symbolic link or updates an existing symlink to
point at the requested source. The default behavior is conservative: Automax
refuses to replace an existing symlink that points somewhere else unless
`force: true` is set, and it refuses to replace a regular file or directory
unless both `force: true` and `allow_replace_non_symlink: true` are set.

`fs.symlink.remove` removes symlinks only. If the path is missing, it succeeds
as already absent. If the path exists but is a file or directory, it fails.

```yaml
- id: switch_current
  use: fs.symlink.create
  with:
    src: /opt/myapp/releases/2026-05-22
    dest: /opt/myapp/current
    force: true
    sudo: true

- id: remove_current_link
  use: fs.symlink.remove
  with:
    path: /opt/myapp/current
    sudo: true
```

## `fs.path.find`

Finds paths under a root path.

```yaml
- id: find_logs
  use: fs.path.find
  with:
    path: /var/log/myapp
    name: "*.log"
    type: file
  register:
    log_files: data.paths
```

## `fs.permission.owner.set` and `fs.permission.mode.set`

Manage ownership and permissions.

```yaml
- id: fix_owner
  use: fs.permission.owner.set
  with:
    path: /opt/myapp
    owner: myapp
    group: myapp
    recursive: true
    sudo: true

- id: fix_mode
  use: fs.permission.mode.set
  with:
    path: /opt/myapp/bin/myapp
    mode: "0755"
    sudo: true
```

## File operation working directories

`fs.file.read`, `fs.file.write`, `fs.file.template`, `fs.file.line`,
`fs.file.line.check` and `fs.file.replace` accept `cwd` for relative remote
paths where applicable. `fs.file.read` also accepts `sudo` for privileged reads.

## Line predicate checks

`fs.file.line.check` checks whether an exact line is present or absent without
modifying the file. It returns `data.matches=true|false` and only fails for
technical errors such as unreadable files or invalid parameters.

## Symlink readback and target checks

`fs.symlink.get` reads the literal symlink target, the resolved target path,
and whether the link is currently broken. Broken links are reported with
`data.broken=true` and `data.target_exists=false`; they are not failures because
cluster active/passive layouts can intentionally point at targets that are not
mounted on the current node.

`fs.symlink.check` keeps predicate semantics: absence or target mismatch returns
`ok=true` with `data.exists=false` or `data.matches=false`. It fails only when
the checked path exists but is not a symlink, because that is an incompatible
filesystem type for this plugin.

## Idempotent ACL and attribute setters

`fs.acl.set` and `fs.attr.set` check the current non-recursive state before
applying changes. If the requested ACL entry or attribute state is already
satisfied, they return `changed=false`. Recursive ACL/attribute operations still
apply the command to the tree because a single root-level predicate is not enough
to prove every descendant already matches.

## Operational backups

`data.backup.file.create` creates an explicit remote backup copy and checksum before risky
maintenance operations. `data.backup.directory.create` creates compressed tar archives with optional checksums. Backup operations are intentionally separate from file
mutation plugins so operators can preview and run them as dedicated steps.

`data.backup.manifest.create` creates a deterministic inventory for backup artifacts, with
optional per-file checksums. `data.backup.prune` removes old artifacts by age or
retention count and requires `confirm: true`. `data.backup.rotate` rotates one backup
artifact through numbered generations and also requires `confirm: true`.

`data.restore.apply` restores an explicit file or archive backup and requires `confirm: true`.
Use `data.restore.preview` before restore to inspect what would be restored,
and `data.restore.verify` after restore to verify restored content against the
backup artifact. `data.backup.verify` validates checksum sidecars as a read-only
post-backup or pre-restore gate.

`storage.mount.bind` manages runtime bind mounts and optional `/etc/fstab` persistence.
`storage.usage.disk.check` is a read-only disk usage gate for preflight checks.
`storage.usage.inode.check` is a read-only inode exhaustion gate for preflight checks and supports `min_free_inodes`, `min_free_percent` and `max_used_percent`.

## File ACL operations

Automax provides POSIX ACL operations for shared directories and service-user
access models:

```text
fs.acl.set      # set or remove ACL entries with optional getfacl backup
fs.acl.get      # read ACLs with getfacl
fs.acl.check    # read-only check for present/absent ACL entries
fs.acl.restore  # restore ACLs from a getfacl backup file
```

Use `fs.acl.get` before changes and `fs.acl.check` after changes when ACLs are
part of the expected system state. `fs.acl.restore` is intended for explicit
restore points generated by `getfacl -p`, not for broad chmod-style permission
rewrites.

## File attribute operations

Automax exposes Linux attribute operations as a small `fs.attr.*` family:

```text
fs.attr.set    # set or clear attributes with chattr
fs.attr.get    # read attributes with lsattr
fs.attr.check  # read-only check for present/absent attributes
```

Use `attrs` without the `+` or `-` prefix; `state: present|absent` selects
whether Automax renders `chattr +<attrs>` or `chattr -<attrs>`.

## Removal semantics

The old generic remover has been replaced by type-strict removal plugins:

```text
fs.dir.remove
fs.file.remove
fs.symlink.remove
```

Each remover succeeds when the path is already absent, but fails when the path
exists with a different type. `fs.dir.remove` uses `rmdir` by default and accepts
`recursive: true` for non-empty directory trees. Directory removal refuses
protected root-level paths such as `/`, `/etc`, `/usr`, `/var` and `/tmp`.

## File mutation validation

`fs.file.write`, `fs.file.template`, `fs.file.line` and `fs.file.replace` support validation commands
and backup-before semantics for configuration file edits. `fs.file.write` and
`fs.file.template` expose an explicit `atomic` option, defaulting to true, so generated
content is installed through a temporary path and final rename where possible.
`fs.file.replace` also supports `required_match_count` to prevent zero-match or
broad-match regex changes.
