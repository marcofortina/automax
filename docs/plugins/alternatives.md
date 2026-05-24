<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Alternatives plugins

Use these plugins for Linux alternatives without hiding distro differences between
Debian-style `update-alternatives` and RHEL-style `alternatives`.

## Read-only inventory

`alternatives.list` returns the alternatives known on the target. On Debian-like
systems it renders `update-alternatives --get-selections`; on RHEL-like systems it
falls back to the alternatives state directories because the native tool is
name-oriented.

`alternatives.get` reads one alternative name with `update-alternatives --query`
or `alternatives --display`. It is read-only and is suitable for prechecks before
changing a selected implementation.

## Mutating selection

`alternatives.set` selects the implementation path for one alternative name. Use
`alternatives.get` first when a job needs to prove the current value before
changing it.

```yaml
use: alternatives.get
with:
  name: java

---
use: alternatives.set
with:
  name: java
  path: /usr/lib/jvm/java-21/bin/java
  sudo: true
```
