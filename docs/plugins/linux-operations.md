<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Linux operations

Automax includes Linux operation macros for storage and Linux prerequisites plus other
enterprise installation jobs where the job must expose concrete commands,
preflight checks and safe backups.

## Block storage

Use `storage.block.facts` and `storage.block.identity` before touching storage. `storage.block.identity`
wraps the stable SCSI identity workflow, including commands such as:

```bash
/usr/lib/udev/scsi_id -g -u -d /dev/sdb1
```

Partition operations are intentionally conservative:

```yaml
use: storage.block.partition.apply
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

`storage.block.partition.apply` creates an `sfdisk --dump` backup when `backup: true`, refuses
mounted devices, calls `partprobe` with `blockdev --rereadpt` fallback, and waits
for `udevadm settle` by default.

For destructive signature cleanup use `storage.block.signatures.wipe`; it requires
`force: true` and stores `wipefs -n` output before applying `wipefs -a` unless
backup is disabled explicitly.

## UDEV and multipath

Use `device.udev.rule.set`, `device.udev.reload`, `device.udev.trigger`, and `device.udev.settle` to make stable
device names explicit and repeatable. `device.udev.rule.set` supports structured rules and
backs up the previous rules file by default.

Use `storage.multipath.status` before storage-dependent operations to verify expected path counts, `storage.multipath.add` when the job owns a new WWID binding, and `storage.multipath.reload` or `storage.multipath.remove` when the job explicitly owns that action.

## Swap, limits, hosts, resolver and chrony

The following macros manage common database/cluster prerequisites with backups
where they modify system files:

```text
storage.swap.add / storage.swap.remove
os.limits.dropin
security.pam.limits
security.pam.access / security.pam.faillock / security.pam.pwhistory / security.pam.succeed_if
security.pam.service_line / security.pam.validate / security.pam.stack.facts / security.authselect.check
os.hosts.entry.add
os.hostname.set
network.dns.config
os.time.chrony.servers.set / os.time.chrony.sources.check
```

`network.dns.config` is deliberately careful: with `backend: auto`, it refuses to
replace a symlinked `/etc/resolv.conf` unless `force: true` or an explicit backend
is provided. This avoids corrupting systems managed by systemd-resolved,
NetworkManager, resolvconf or cloud-init.

## Environment, reboot and downloads

`os.env.set` can set step-scoped variables for later remote commands, or persistent
variables in a global/profile file:

```yaml
use: os.env.set
with:
  scope: global
  variables:
    APP_HOME: /opt/app
    APP_CONFIG_DIR: /etc/app
  sudo: true
```

`system.reboot` requests a reboot. Use the rendered manual command and follow-up
connectivity, process and service check substeps to validate that SSH and services are back.

`data.download.url` is the remote wget/curl-like macro. It downloads with curl or
wget, supports SHA256 verification, backs up an existing destination by default,
and can install mode/owner/group metadata.


## LVM storage

Use `storage.lvm.pv.add`, `storage.lvm.vg.add`, `storage.lvm.lv.add`, `storage.lvm.lv.extend`, `storage.lvm.pv.scan`, `storage.lvm.vg.scan`, `storage.lvm.lv.scan` and `storage.fs.resize` for physical volumes, volume groups, logical volumes, metadata scan and filesystem growth. These macros expose deterministic manual commands and
structured `plan --diff` previews before applying storage changes.


## Runtime network operations

Use `network.link.interface`, `network.link.bond`, `network.link.bridge`, `network.link.vlan`,
`network.route.add`, `network.route.remove` and `network.dns.config` for runtime network setup
and DNS resolver changes. DNS handling is
backend-aware through the same safety rules as `network.dns.config`: managed or
symlinked resolver files are not overwritten silently.


## Runtime service checks

Use `network.connectivity.port.check` for target-side TCP/UDP connectivity checks,
`network.http.request` for controller-side HTTP probes, and the `system.process.*` family for
process lifecycle checks. The former service-health wrapper namespace is
intentionally not part of the public plugin surface.


## Certificate and PKI operations

Use `security.pki.trust.install_ca`, `security.pki.key.permissions` and `security.pki.cert.expiry.check` to
install CA certificates, enforce private-key permissions and validate certificate
expiry windows. File-changing operations include preview data and backups where
applicable.


## Package locks and pinning

Use `os.package.hold.add`, `os.package.hold.remove`, `os.package.version.pin` and `os.package.repo.priority.set` to lock
packages, pin versions and manage repository priorities across supported package
managers. File-backed pinning and priority files are previewable and backed up by
default.


## Advanced mounts and filesystem resizing

Use `storage.mount.remount`, `storage.fs.resize` and `storage.mount.check` to remount filesystems,
grow supported filesystems and check current runtime mount state with `findmnt`.
Runtime mount state lives under `storage.mount.*`; persistent boot-time mount and
swap configuration lives under `storage.fstab.*`.


## Logs and journal collection

Use `system.log.grep`, `system.journal.collect`, `system.journal.grep` and `system.log.export` to inspect
logs, grep journal output and emit stdout suitable for artifact capture. These
macros are read-oriented and document why no file diff is emitted.


## Controller-side mail notifications

Use `notify.mail.send` to send SMTP notifications from the Automax controller. It does
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
include fstab plans for `storage.swap.add` / `storage.swap.remove`, PAM append plans for
`security.pam.limits`, hostname and download plans, and runtime explanations for
`storage.block.scan`, `device.udev.reload`, `storage.multipath.reload` and `system.reboot`.

## Enterprise system operations

Automax also includes higher-level Linux operations for enterprise-style host
preparation and recovery workflows. These plugins are still plain Automax
substeps: they support operator previews, copy/pasteable command rendering, and
backup/validation guards where the underlying operation changes persistent host
configuration.

Useful families include:

```text
os.platform.facts
network.dns.facts
network.link.facts / network.route.facts
os.package.version.pin / os.package.repo.priority.set
network.link.interface / network.link.bond / network.link.vlan / network.route.add / network.route.remove with persist/backend
security.pki.trust.install_ca with trust_store=system
storage.lvm.lv.snapshot / storage.lvm.lv.thin_pool / storage.lvm.lv.remove / storage.lvm.vg.remove / storage.lvm.pv.remove
fs.acl.set / fs.attr.set / storage.quota.set / storage.quota.get / storage.quota.check / storage.quota.facts
system.systemd.unit / system.systemd.timer / system.systemd.tmpfiles / system.systemd.sysusers
os.alternatives.set
security.audit.rule / security.audit.status / security.audit.reload
security.ssh.config / security.ssh.known_hosts / security.ssh.authorized_key.add / security.ssh.authorized_key.check
security.selinux.port / security.selinux.fcontext
system.kernel.boot_param.add
security.sudo.rule / security.sudo.validate
```

Destructive plugins such as LVM removal require explicit confirmation parameters.
Persistent file-oriented operations create backups by default when they replace
existing configuration files.

## iptables

`network.firewall.iptables.rule` manages legacy iptables/ip6tables runtime rules as a backend separate from firewalld, UFW and nftables.
`network.firewall.iptables.save` exports the current runtime ruleset to an explicit persistent file.
`network.firewall.iptables.restore` loads an explicit ruleset file and requires `confirm: true` unless `test_only: true`.

## Certificate operations

`security.pki.csr.generate` creates CSRs from existing keys using openssl.
`security.pki.cert.self_signed` generates self-signed certificates from existing private keys.
`security.pki.cert.chain.check` performs read-only openssl chain verification.
`security.pki.cert.install_keypair` installs certificate/key pairs with private-key mode `0600`.
`security.pki.cert.expiry_report` reads certificate expiry and fails when inside the configured warning window.

## Network checks, facts and bridge operations

Use `network.link.bridge` for explicit runtime bridge creation/removal. Use
`network.link.check`, `network.route.check`, `network.dns.check` and
`network.connectivity.port.check` as precheck/postcheck guards around network operations.
Use `network.link.facts` and `network.route.facts` for read-only iproute2 JSON
readback without treating mismatched state as a failed assertion.

## Udev, time and account readback

Udev validation/readback plugins are `device.device.udev.rule.set.validate`, `device.udev.device.test` and
`device.udev.device.facts`. Use them before and after installing udev rules.

Time synchronization helpers include `os.time.status`,
`os.time.timezone.set`, `os.time.ntp.set` and `os.time.chrony.tracking.check`.

User and group readback/assertion plugins include `identity.user.facts`,
`identity.user.shell.check`, `identity.user.home.check`, `identity.user.groups.check`, `identity.group.member.list`
and `identity.group.member.remove`. Removing a group member requires `confirm: true`.

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
