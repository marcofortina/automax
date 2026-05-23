<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Linux security modules

Automax supports SELinux and AppArmor workflows without hiding distribution differences.

## SELinux

```yaml
- id: allow_http_network
  use: selinux.boolean
  with:
    name: httpd_can_network_connect
    value: true
    persist: true
    sudo: true
```

Available plugins include `selinux.mode`, `selinux.boolean`, `selinux.context` and `selinux.restorecon`.

## AppArmor

```yaml
- id: enforce_nginx_profile
  use: apparmor.profile
  with:
    profile: /etc/apparmor.d/usr.sbin.nginx
    state: enforce
    sudo: true
```

Available plugins include `apparmor.status`, `apparmor.profile` and `apparmor.reload`.
