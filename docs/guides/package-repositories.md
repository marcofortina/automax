<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Package repositories

Automax manages package repository keys and repository definitions for Debian/Ubuntu and Red Hat-like systems.

```yaml
- id: install_vendor_key
  use: os.package.key.add
  with:
    name: vendor
    manager: apt
    url: https://repo.example/key.gpg
    sudo: true
```

```yaml
- id: add_vendor_apt_repo
  use: os.package.repo.add
  with:
    name: vendor
    manager: apt
    repo: deb [signed-by=/etc/apt/keyrings/vendor.gpg] https://repo.example stable main
    update_cache: true
    sudo: true
```

For RHEL-like systems, provide a `.repo` file body with `content` or `src` and `manager: dnf` or `manager: yum`.

```yaml
- id: add_vendor_dnf_repo
  use: os.package.repo.add
  with:
    name: vendor
    manager: dnf
    content: |
      [vendor]
      name=Vendor packages
      baseurl=https://repo.example/rhel/$releasever/$basearch
      enabled=1
      gpgcheck=1
      gpgkey=https://repo.example/RPM-GPG-KEY-vendor
    update_cache: true
    sudo: true
```
