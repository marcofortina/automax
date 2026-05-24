<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Builtin plugins

Only canonical plugin names are part of the public DSL. Compatibility aliases are
not exposed as public plugin names.

Use the CLI to inspect the installed plugin registry:

```bash
automax plugins list
```

Current builtin plugins:

```text
alternatives.set
apparmor.profile
apparmor.reload
apparmor.status
archive.compress
archive.decompress
archive.tar
archive.untar
archive.unzip
archive.zip
assert.command
assert.disk
assert.file
assert.path
assert.tcp
auditd.reload
auditd.rule
auditd.status
backup.directory
backup.file
backup.restore
block.facts
block.identity
block.mkfs
block.partition
block.partition_rescan
block.rescan
block.wipe_signatures
chrony.servers
chrony.sources_assert
cron.entry
cron.file
db.health
db.mysql.query
db.oracle.query
db.postgres.query
db.sqlite.query
download.file
env.set
facts.gather
facts.network
facts.os
facts.packages
facts.services
findmnt.assert
firewalld.port
firewalld.reload
firewalld.rich_rule
firewalld.service
fs.acl
fs.attr
fs.cd
fs.chmod
fs.chown
fs.copy
fs.exists
fs.find
fs.line
fs.mkdir
fs.move
fs.quota
fs.read
fs.remove
fs.replace
fs.resize
fs.stat
fs.symlink.create
fs.symlink.remove
fs.template
fs.write
fstab.entry
group.create
group.exists
group.remove
health.http
health.listen
health.port
health.process
hostname.set
hosts.entry
http.assert
http.request
http.wait
journal.collect
journal.grep
kernel.boot_param
kernel.module.load
kernel.module.persist
kernel.module.unload
limits.dropin
local.command
log.export
log.grep
lvm.lv_extend
lvm.lv_present
lvm.lv_remove
lvm.pv_present
lvm.pv_remove
lvm.resizefs
lvm.snapshot
lvm.thin_pool
lvm.vg_present
lvm.vg_remove
mail.send
mount.absent
mount.present
mount.remount
multipath.flush
multipath.reload
multipath.status
network.bond
network.dns
network.interface
network.route
network.vlan
nftables.apply
nftables.validate
pam.limits
pkg.hold
pkg.install
pkg.key.add
pkg.key.remove
pkg.query
pkg.remove
pkg.repo.add
pkg.repo.remove
pkg.repo_priority
pkg.unhold
pkg.update_cache
pkg.upgrade
pkg.version_pin
pki.ca_install
pki.cert_expiry_assert
pki.key_permissions
platform.facts
process.kill
process.wait
remote.command
resolver.config
resolver.facts
selinux.boolean
selinux.context
selinux.fcontext
selinux.mode
selinux.port
selinux.restorecon
ssh.authorized_key
ssh.config
ssh.known_hosts
sudo.rule
sudo.validate
sudoers.dropin
swap.absent
swap.present
sysctl.get
sysctl.persist
sysctl.reload
sysctl.set
system.reboot
systemctl.daemon_reload
systemctl.disable
systemctl.enable
systemctl.is_active
systemctl.is_enabled
systemctl.mask
systemctl.reload
systemctl.restart
systemctl.start
systemctl.status
systemctl.stop
systemctl.unmask
systemd.sysusers
systemd.timer
systemd.tmpfiles
systemd.unit
transfer.download
transfer.rsync
transfer.sync
transfer.upload
udev.reload
udev.rule
udev.settle
udev.trigger
ufw.disable
ufw.enable
ufw.rule
ufw.status
user.create
user.exists
user.lock
user.modify
user.remove
user.set_password
user.unlock
wait.command
wait.file
wait.path
wait.process
wait.tcp

```

## Manuals by category

- [Generated plugin reference](generated.md)
- [Commands](commands.md)
- [Filesystem](filesystem.md)
- [Linux operations](linux-operations.md)
- [Archive](archive.md)
- [Package manager](package-manager.md)
- [Systemctl](systemctl.md)
- [Users, groups and processes](users-groups-processes.md)
- [Transfer](transfer.md)
- [HTTP/API](http-api.md)
- [Wait and assert](wait-assert.md)
- [Database](database.md)
- [Extended SSH Smoke](../guides/ssh-smoke.md)

External plugin modules can be added through the registry mechanism without
changing the core execution engine.
