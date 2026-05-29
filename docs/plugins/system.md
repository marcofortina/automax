<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# System plugins

`system.service.*` plugins manage systemd units on the remote target. Use `sudo: true` for system services. Use `user: true` for `systemctl --user` operations.

## Lifecycle

```yaml
- id: start_service
  use: system.service.start
  with:
    service: nginx.service
    sudo: true

- id: stop_service
  use: system.service.stop
  with:
    service: nginx.service
    sudo: true

- id: restart_service
  use: system.service.restart
  with:
    service: nginx.service
    sudo: true

- id: reload_service
  use: system.service.reload
  with:
    service: nginx.service
    sudo: true
```

`start` and `stop` check the current state first. `restart`, `reload` and
`system.systemd.daemon.reload` marks the substep changed when they run.

## Enablement and masking

```yaml
- id: enable_service
  use: system.service.enable
  with:
    service: nginx.service
    sudo: true

- id: disable_service
  use: system.service.disable
  with:
    service: nginx.service
    sudo: true

- id: mask_service
  use: system.service.mask
  with:
    service: old.service
    sudo: true

- id: unmask_service
  use: system.service.unmask
  with:
    service: old.service
    sudo: true
```

## Status checks

```yaml
- id: get_status
  use: system.service.status
  with:
    service: nginx.service
  register:
    nginx_status: stdout.trim

- id: is_active
  use: system.service.active.check
  with:
    service: nginx.service

- id: is_enabled
  use: system.service.enabled.check
  with:
    service: nginx.service
```

## Daemon reload

```yaml
- id: daemon_reload
  use: system.systemd.daemon.reload
  with:
    sudo: true
```


`system.service.active.check` and `system.service.enabled.check` return `ok=true` when the query runs successfully and expose the service state in `data.active` or `data.enabled`.
