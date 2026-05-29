<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# OS alternatives plugins

Use these plugins for Linux alternatives without hiding distro differences between
Debian-style `update-alternatives` and RHEL-style `alternatives`.

## Read-only inventory

`os.alternatives.list` returns the alternatives known on the target. On Debian-like
systems it renders `update-alternatives --get-selections`; on RHEL-like systems it
falls back to the alternatives state directories because the native tool is
name-oriented.

`os.alternatives.get` reads one alternative name with `update-alternatives --query`
or `alternatives --display`. `os.alternatives.check` asserts that the selected
implementation already points to the expected path.

## Mutating selection

`os.alternatives.set` selects the implementation path for one alternative name. Use
`os.alternatives.get` first when a job needs to prove the current value before
changing it.

```yaml
use: os.alternatives.check
with:
  name: java
  path: /usr/lib/jvm/java-21/bin/java

---
use: os.alternatives.set
with:
  name: java
  path: /usr/lib/jvm/java-21/bin/java
  sudo: true
```
