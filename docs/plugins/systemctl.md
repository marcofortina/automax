# Systemctl plugins

Systemctl plugins manage systemd units on the remote target. Use `sudo: true`
for system services.

## Lifecycle

```yaml
- id: start_service
  use: systemctl.start
  with:
    service: nginx.service
    sudo: true

- id: stop_service
  use: systemctl.stop
  with:
    service: nginx.service
    sudo: true

- id: restart_service
  use: systemctl.restart
  with:
    service: nginx.service
    sudo: true

- id: reload_service
  use: systemctl.reload
  with:
    service: nginx.service
    sudo: true
```

`start` and `stop` check the current state first. `restart`, `reload` and
`daemon_reload` mark the substep changed when they run.

## Enablement and masking

```yaml
- id: enable_service
  use: systemctl.enable
  with:
    service: nginx.service
    sudo: true

- id: disable_service
  use: systemctl.disable
  with:
    service: nginx.service
    sudo: true

- id: mask_service
  use: systemctl.mask
  with:
    service: old.service
    sudo: true

- id: unmask_service
  use: systemctl.unmask
  with:
    service: old.service
    sudo: true
```

## Status checks

```yaml
- id: get_status
  use: systemctl.status
  with:
    service: nginx.service
  register:
    nginx_status: stdout.trim

- id: is_active
  use: systemctl.is_active
  with:
    service: nginx.service

- id: is_enabled
  use: systemctl.is_enabled
  with:
    service: nginx.service
```

## Daemon reload

```yaml
- id: daemon_reload
  use: systemctl.daemon_reload
  with:
    sudo: true
```
