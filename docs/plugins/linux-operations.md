<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Linux operations

Automax includes Linux operation macros for storage and Linux prerequisites plus other
enterprise installation jobs where the job must expose concrete commands,
preflight checks and safe backups.

## Block storage

Use `block.facts` and `block.identity` before touching storage. `block.identity`
wraps the stable SCSI identity workflow, including commands such as:

```bash
/usr/lib/udev/scsi_id -g -u -d /dev/sdb1
```

Partition operations are intentionally conservative:

```yaml
use: block.partition
with:
  device: /dev/sdb
  label: gpt
  backup: true
  partitions:
    - number: 1
      name: DATA01
      start: 1MiB
      end: 100%
  sudo: true
```

`block.partition` creates an `sfdisk --dump` backup when `backup: true`, refuses
mounted devices, calls `partprobe` with `blockdev --rereadpt` fallback, and waits
for `udevadm settle` by default.

For destructive signature cleanup use `block.wipe_signatures`; it requires
`force: true` and stores `wipefs -n` output before applying `wipefs -a` unless
backup is disabled explicitly.

## UDEV and multipath

Use `udev.rule`, `udev.reload`, `udev.trigger`, and `udev.settle` to make stable
device names explicit and repeatable. `udev.rule` supports structured rules and
backs up the previous rules file by default.

Use `multipath.status` before storage-dependent operations to verify expected path
counts, then `multipath.reload` or `multipath.flush` when the job explicitly owns
that action.

## Swap, limits, hosts, resolver and chrony

The following macros manage common database/cluster prerequisites with backups
where they modify system files:

```text
swap.present / swap.absent
limits.dropin
pam.limits
hosts.entry
hostname.set
resolver.config
chrony.servers / chrony.sources_assert
```

`resolver.config` is deliberately careful: with `backend: auto`, it refuses to
replace a symlinked `/etc/resolv.conf` unless `force: true` or an explicit backend
is provided. This avoids corrupting systems managed by systemd-resolved,
NetworkManager, resolvconf or cloud-init.

## Environment, reboot and downloads

`env.set` can set step-scoped variables for later remote commands, or persistent
variables in a global/profile file:

```yaml
use: env.set
with:
  scope: global
  variables:
    APP_HOME: /opt/app
    APP_CONFIG_DIR: /etc/app
  sudo: true
```

`system.reboot` requests a reboot. Use the rendered manual command and follow-up
wait/assert substeps to validate that SSH and services are back.

`download.file` is the remote wget/curl-like macro. It downloads with curl or
wget, supports SHA256 verification, backs up an existing destination by default,
and can install mode/owner/group metadata.

## Recovery workflow

All Linux operation macros should be used with the operator recovery commands:

```bash
automax plan --check --job jobs/linux-preflight.yaml --inventory inventory/prod.yaml
automax plan --diff --job jobs/linux-preflight.yaml --inventory inventory/prod.yaml
automax commands render --job jobs/linux-preflight.yaml --inventory inventory/prod.yaml --limit app1
```
