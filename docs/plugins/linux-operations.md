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
pam.access / pam.faillock / pam.pwhistory / pam.succeed_if
pam.service_line / pam.validate / pam.stack_facts / pam.authselect
hosts.entry
hostname.set
network.dns
chrony.servers / chrony.sources_assert
```

`network.dns` is deliberately careful: with `backend: auto`, it refuses to
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


## LVM storage

Use `lvm.pv_present`, `lvm.vg_present`, `lvm.lv_present`, `lvm.lv_extend`
and `lvm.resizefs` for physical volumes, volume groups, logical volumes and
filesystem growth. These macros expose deterministic manual commands and
structured `plan --diff` previews before applying storage changes.


## Runtime network operations

Use `network.link.interface`, `network.link.bond`, `network.link.bridge`, `network.link.vlan`,
`network.route.add`, `network.route.remove` and `network.dns` for runtime network setup
and DNS resolver changes. DNS handling is
backend-aware through the same safety rules as `network.dns`: managed or
symlinked resolver files are not overwritten silently.


## Runtime service checks

Use `network.connectivity.port_check` for target-side TCP/UDP connectivity checks,
`http.request` for controller-side HTTP probes, and the `process.*` family for
process lifecycle checks. The former service-health wrapper namespace is
intentionally not part of the public plugin surface.


## Certificate and PKI operations

Use `pki.ca_install`, `pki.key_permissions` and `pki.cert_expiry_assert` to
install CA certificates, enforce private-key permissions and validate certificate
expiry windows. File-changing operations include preview data and backups where
applicable.


## Package locks and pinning

Use `pkg.hold`, `pkg.unhold`, `pkg.version_pin` and `pkg.repo_priority` to lock
packages, pin versions and manage repository priorities across supported package
managers. File-backed pinning and priority files are previewable and backed up by
default.


## Advanced mounts and filesystem resizing

Use `mount.remount`, `fs.resize` and `findmnt.assert` to remount filesystems,
grow supported filesystems and assert current mount state with `findmnt`. Runtime
operations provide state previews and manual recovery commands.


## Logs and journal collection

Use `log.grep`, `journal.collect`, `journal.grep` and `log.export` to inspect
logs, grep journal output and emit stdout suitable for artifact capture. These
macros are read-oriented and document why no file diff is emitted.


## Controller-side mail notifications

Use `mail.send` to send SMTP notifications from the Automax controller. It does
not open a remote SSH session, it never renders SMTP passwords in manual command
output, and attachments are read from local controller paths.

## Recovery workflow

All Linux operation macros should be used with the operator recovery commands:

```bash
automax plan --check --job jobs/linux-preflight.yaml --inventory inventory/prod.yaml
automax plan --diff --job jobs/linux-preflight.yaml --inventory inventory/prod.yaml
automax commands render --job jobs/linux-preflight.yaml --inventory inventory/prod.yaml --limit app1
```

`plan --diff` now represents the whole selected job shape for these macros:
file-backed operations emit deterministic unified diffs or structured state
plans, while runtime-only/read-only operations emit explicit reasons. Examples
include fstab plans for `swap.present` / `swap.absent`, PAM append plans for
`pam.limits`, hostname and download plans, and runtime explanations for
`block.rescan`, `udev.reload`, `multipath.reload` and `system.reboot`.

## Enterprise system operations

Automax also includes higher-level Linux operations for enterprise-style host
preparation and recovery workflows. These plugins are still plain Automax
substeps: they support operator previews, copy/pasteable command rendering, and
backup/validation guards where the underlying operation changes persistent host
configuration.

Useful families include:

```text
platform.facts
network.dns_facts
network.link.facts / network.route.facts
pkg.version_pin / pkg.repo_priority
network.link.interface / network.link.bond / network.link.vlan / network.route.add / network.route.remove with persist/backend
pki.ca_install with trust_store=system
lvm.snapshot / lvm.thin_pool / lvm.lv_remove / lvm.vg_remove / lvm.pv_remove
fs.acl / fs.attr / fs.quota
systemd.unit / systemd.timer / systemd.tmpfiles / systemd.sysusers
alternatives.set
auditd.rule / auditd.status / auditd.reload
ssh.config / ssh.known_hosts / ssh.authorized_key
selinux.port / selinux.fcontext
kernel.boot_param
sudo.rule / sudo.validate
```

Destructive plugins such as LVM removal require explicit confirmation parameters.
Persistent file-oriented operations create backups by default when they replace
existing configuration files.

## iptables

`network.firewall.iptables.rule` manages legacy iptables/ip6tables runtime rules as a backend separate from firewalld, UFW and nftables.
`network.firewall.iptables.save` exports the current runtime ruleset to an explicit persistent file.
`network.firewall.iptables.restore` loads an explicit ruleset file and requires `confirm: true` unless `test_only: true`.

## Certificate operations

`cert.generate_csr` creates CSRs from existing keys using openssl.
`cert.self_signed` generates self-signed certificates from existing private keys.
`cert.verify_chain` performs read-only openssl chain verification.
`cert.install_keypair` installs certificate/key pairs with private-key mode `0600`.
`cert.expiry_report` reads certificate expiry and fails when inside the configured warning window.

## Network checks, facts and bridge operations

Use `network.link.bridge` for explicit runtime bridge creation/removal. Use
`network.link.check`, `network.route.check`, `network.dns_assert` and
`network.connectivity.port_check` as precheck/postcheck guards around network operations.
Use `network.link.facts` and `network.route.facts` for read-only iproute2 JSON
readback without treating mismatched state as a failed assertion.

## Udev, time and account readback

Udev validation/readback plugins are `udev.validate`, `udev.test` and
`udev.facts`. Use them before and after installing udev rules.

Time synchronization helpers include `timedatectl.status`,
`timedatectl.timezone`, `timedatectl.ntp` and `chrony.tracking_assert`.

User and group readback/assertion plugins include `user.facts`,
`user.shell_assert`, `user.home_assert`, `user.groups_assert`, `group.members`
and `group.member_absent`. Removing a group member requires `confirm: true`.

## OS-aware job-scoped capability preflight

Automax can derive remote command dependencies from the selected job plan and render per-target checks. Automax first reads `/etc/os-release` on each target, classifies it as DEBIAN-like or RHEL-like, filters backend-specific plugins for that OS family, and reports OS-mismatched plugins as skipped requirements instead of requiring irrelevant tools.

```bash
automax capabilities requirements --job jobs/site.yaml --inventory inventory/prod.yaml
```

Normal `automax run` performs this OS detection and capability preflight implicitly before executing selected substeps. The older `--preflight-capabilities` flag remains accepted for compatibility, but the preflight is now the default for normal runs that require remote tools. If selected substeps use `sudo` and the target account requires a password, run with `--sudo-password-env ENV_NAME` instead of installing a NOPASSWD sudoers drop-in.

```bash
export AUTOMAX_SUDO_PASSWORD='...'
automax run \
  --job jobs/site.yaml \
  --inventory inventory/prod.yaml \
  --sudo-password-env AUTOMAX_SUDO_PASSWORD
```

Missing dependencies can be installed per target from the OS-aware requirement plan:

```bash
export AUTOMAX_SUDO_PASSWORD='...'
automax capabilities install \
  --job jobs/site.yaml \
  --inventory inventory/prod.yaml \
  --sudo-password-env AUTOMAX_SUDO_PASSWORD
```

Only packages for tools that are actually missing on each target are installed. OS-mismatched plugins are not installed for that target.
