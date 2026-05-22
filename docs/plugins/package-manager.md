<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Package manager plugins

Package plugins run on the remote target and support `apt`, `apt-get`, `dnf`,
`yum`, `zypper` and `pacman`. Use `manager: auto` unless you need to force a
specific backend. Package plugins default to `sudo: true` because package managers normally require privilege escalation.

## `pkg.update_cache`

Refreshes package metadata.

```yaml
- id: update_cache
  use: pkg.update_cache
  with:
    manager: auto
    sudo: true
```

## `pkg.install`

Installs one or more packages only when missing.

```yaml
- id: install_packages
  use: pkg.install
  with:
    packages:
      - nginx
      - curl
    manager: auto
    sudo: true
```

## `pkg.remove`

Removes one or more packages only when installed.

```yaml
- id: remove_telnet
  use: pkg.remove
  with:
    name: telnet
    manager: auto
    sudo: true
```

## `pkg.upgrade`

Runs a package upgrade through the selected manager.

```yaml
- id: upgrade_system
  use: pkg.upgrade
  with:
    manager: apt-get
    sudo: true
```

## `pkg.query`

Returns package installation state without changing the host.

```yaml
- id: query_packages
  use: pkg.query
  with:
    packages: [nginx, curl]
  register:
    package_state: stdout.trim
```
