<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Users, groups and processes

These plugins run on the remote target through SSH.

## Groups

```yaml
- id: create_group
  use: identity.group.create
  with:
    name: myapp
    system: true
    sudo: true

- id: remove_group
  use: identity.group.remove
  with:
    name: oldgroup
    sudo: true
```

## Users

```yaml
- id: create_user
  use: identity.user.create
  with:
    name: myapp
    group: myapp
    home: /var/lib/myapp
    shell: /usr/sbin/nologin
    system: true
    sudo: true

- id: modify_user
  use: identity.user.modify
  with:
    name: myapp
    shell: /bin/bash
    sudo: true

- id: remove_user
  use: identity.user.remove
  with:
    name: olduser
    remove_home: true
    sudo: true
```

## Processes

```yaml
- id: wait_for_worker
  use: system.process.wait
  with:
    pattern: "myapp-worker"
    state: present
    timeout: 60
    interval: 2

- id: stop_old_worker
  use: system.process.kill
  with:
    pattern: "old-worker"
    signal: TERM
    sudo: true
```

`system.process.signal` sends a runtime signal by PID or pattern and renders the exact manual command for recovery.
`system.process.check` is a read-only pgrep assertion used as a pre/post check.
`system.process.count_check` gates process cardinality with exact, minimum or maximum count checks.

`security.sshd.config` installs server-side SSH hardening drop-ins and validates them with `sshd -t` before reload.
`login.defs` manages account-aging defaults in `/etc/login.defs` with backup.
`security.password.policy` installs pwquality drop-ins for password complexity policy.
`security.authselect.profile` selects RHEL-style authentication profiles with explicit backup by default.

## Account assertions and access changes

`identity.user.exists` and `identity.group.exists` are read-only assertions for account prerequisites. `identity.user.lock`, `identity.user.unlock` and `identity.user.set_password` are explicit account state changes and should be reviewed separately from user creation/removal.
