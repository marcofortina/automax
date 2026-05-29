<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# OS package manager plugins

Package plugins run on the remote target and support `apt`, `apt-get`, `dnf`,
`yum`, `zypper` and `pacman`. Use `manager: auto` unless you need to force a
specific backend. Package plugins default to `sudo: true` because package managers normally require privilege escalation.

## `os.package.update_cache`

Refreshes package metadata.

```yaml
- id: update_cache
  use: os.package.update_cache
  with:
    manager: auto
    sudo: true
```

## `os.package.install`

Installs one or more packages only when missing.

```yaml
- id: install_packages
  use: os.package.install
  with:
    packages:
      - nginx
      - curl
    manager: auto
    sudo: true
```

## `os.package.remove`

Removes one or more packages only when installed.

```yaml
- id: remove_telnet
  use: os.package.remove
  with:
    name: telnet
    manager: auto
    sudo: true
```

## `os.package.upgrade`

Runs a package upgrade through the selected manager.

```yaml
- id: upgrade_system
  use: os.package.upgrade
  with:
    manager: apt-get
    sudo: true
```

## `os.package.query`

Returns package installation state without changing the host.

```yaml
- id: query_packages
  use: os.package.query
  with:
    packages: [nginx, curl]
  register:
    package_state: stdout.trim
```

## Repository keys and definitions

Use `os.package.key.add`, `os.package.key.remove`, `os.package.key.list` and `os.package.key.check` for package signing keys. Use `os.package.repo.add`, `os.package.repo.remove`, `os.package.repo.list` and `os.package.repo.check` for repository definitions. Keep key and repository changes in separate substeps so package-manager trust changes remain reviewable.

## Inspection and verification

Use `os.package.check` for installed/absent package checks and `os.package.version.check` to gate a run on an expected installed package version.
Use `os.package.owner` and `os.package.files` for troubleshooting package/file ownership. Use
`os.package.verify` for package-manager integrity checks and `os.package.clean` for explicit
cache cleanup.

## Package lifecycle hardening

`os.package.hold.add`, `os.package.hold.remove`, `os.package.hold.list` and `os.package.hold.check` manage package holds. `os.package.install` supports version pinning during install, temporary repository
selection, no-recommends installs, explicit downgrade allowance and optional lock
after install. `os.package.remove` supports purge/autoremove with `confirm: true` for
risky removals and protected package guards. `os.package.upgrade` supports security-only,
exclude, download-only and reboot-required checks where the selected package
manager supports them.
