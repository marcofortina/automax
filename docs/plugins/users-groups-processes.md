# Users, groups and processes

These plugins run on the remote target through SSH.

## Groups

```yaml
- id: create_group
  use: group.create
  with:
    name: myapp
    system: true
    sudo: true

- id: remove_group
  use: group.remove
  with:
    name: oldgroup
    sudo: true
```

## Users

```yaml
- id: create_user
  use: user.create
  with:
    name: myapp
    group: myapp
    home: /var/lib/myapp
    shell: /usr/sbin/nologin
    system: true
    sudo: true

- id: modify_user
  use: user.modify
  with:
    name: myapp
    shell: /bin/bash
    sudo: true

- id: remove_user
  use: user.remove
  with:
    name: olduser
    remove_home: true
    sudo: true
```

## Processes

```yaml
- id: wait_for_worker
  use: process.wait
  with:
    pattern: "myapp-worker"
    state: present
    timeout: 60
    interval: 2

- id: stop_old_worker
  use: process.kill
  with:
    pattern: "old-worker"
    signal: TERM
    sudo: true
```
