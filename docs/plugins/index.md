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
alternatives.get
alternatives.list
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
authselect.profile
backup.directory
backup.file
backup.restore
backup.verify
block.facts
block.identity
block.mkfs
block.partition
block.partition_rescan
block.rescan
block.wipe_signatures
cert.expiry_report
cert.generate_csr
cert.install_keypair
cert.self_signed
cert.verify_chain
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
firewalld.list
firewalld.port
firewalld.reload
firewalld.rich_rule
firewalld.service
firewalld.status
firewalld.zone
fs.acl
fs.attr
fs.bind_mount
fs.cd
fs.chmod
fs.chown
fs.copy
fs.disk_usage_assert
fs.exists
fs.find
fs.inode_usage_assert
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
iptables.chain
iptables.list
iptables.policy
iptables.restore
iptables.rule
iptables.save
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
login.defs
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
nftables.export
nftables.list
nftables.validate
pam.limits
password.policy
pkg.clean
pkg.files
pkg.hold
pkg.install
pkg.key.add
pkg.key.remove
pkg.owner
pkg.query
pkg.remove
pkg.repo.add
pkg.repo.remove
pkg.repo_priority
pkg.unhold
pkg.update_cache
pkg.upgrade
pkg.verify
pkg.version_assert
pkg.version_pin
pki.ca_install
pki.cert_expiry_assert
pki.key_permissions
platform.facts
process.assert_absent
process.assert_count
process.kill
process.signal
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
ssh.keygen
ssh.known_hosts
sshd.config
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
- [Alternatives](alternatives.md)
- [Firewall](firewall.md)
- [Facts and cron](facts-cron.md)
- [Kernel, mount and storage](kernel-storage.md)
- [Security and access control](security.md)
- [Extended SSH Smoke](../guides/ssh-smoke.md)

External plugin modules can be added through the registry mechanism without
changing the core execution engine.
