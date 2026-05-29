<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Linux security modules

Automax supports SELinux and AppArmor workflows without hiding distribution differences.

## SELinux

```yaml
- id: allow_http_network
  use: security.selinux.boolean
  with:
    name: httpd_can_network_connect
    value: true
    persist: true
    sudo: true
```

Available plugins include `security.selinux.mode`, `security.selinux.boolean`, `security.selinux.context` and `security.selinux.restorecon`.

## AppArmor

```yaml
- id: enforce_nginx_profile
  use: security.apparmor.profile
  with:
    profile: /etc/apparmor.d/usr.sbin.nginx
    state: enforce
    sudo: true
```

Available plugins include `security.apparmor.status`, `security.apparmor.profile` and `security.apparmor.reload`.
