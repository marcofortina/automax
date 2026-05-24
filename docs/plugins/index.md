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
apparmor.complain
apparmor.disable
apparmor.enforce
apparmor.parser_validate
apparmor.profile
apparmor.profile_assert
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
auditd.backlog_assert
auditd.reload
auditd.rule
auditd.rules_facts
auditd.search
auditd.status
auditd.syscall
auditd.watch
authselect.profile
backup.directory
backup.file
backup.restore
backup.verify
blkid.assert
block.empty_assert
block.facts
block.fs_assert
block.identity
block.mkfs
block.mountpoint_assert
block.not_mounted_assert
block.partition
block.partition_rescan
block.rescan
block.size_assert
block.wipe_signatures
cert.expiry_report
cert.fingerprint
cert.generate_csr
cert.install_ca_bundle
cert.install_keypair
cert.issuer_assert
cert.matches_key
cert.san_assert
cert.self_signed
cert.subject_assert
cert.verify_chain
chrony.servers
chrony.sources_assert
chrony.tracking_assert
cron.absent
cron.entry
cron.file
cron.list
cron.validate
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
firewalld.forward_port
firewalld.icmp_block
firewalld.list
firewalld.masquerade
firewalld.port
firewalld.reload
firewalld.rich_rule
firewalld.service
firewalld.source
firewalld.status
firewalld.zone
fs.acl
fs.acl.assert
fs.acl.get
fs.acl.restore
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
fstab.absent
fstab.assert
fstab.entry
fstab.validate
group.create
group.exists
group.member_absent
group.members
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
iptables.counter_assert
iptables.delete
iptables.exists_assert
iptables.list
iptables.policy
iptables.restore
iptables.rule
iptables.save
journal.collect
journal.grep
kernel.boot_param
kernel.boot_param_absent
kernel.cmdline_assert
kernel.module.blacklist
kernel.module.load
kernel.module.persist
kernel.module.status
kernel.module.unload
limits.dropin
local.command
log.export
log.grep
login.defs
lvm.facts
lvm.lv_assert
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
mount.assert
mount.facts
mount.options_assert
mount.present
mount.remount
multipath.flush
multipath.reload
multipath.status
network.bond
network.bridge
network.dns
network.dns_assert
network.interface
network.link_assert
network.port_check
network.route
network.route_assert
network.vlan
nftables.apply
nftables.export
nftables.list
nftables.rollback_file
nftables.ruleset_assert
nftables.validate
pam.access
pam.authselect
pam.backup
pam.faillock
pam.include_assert
pam.limits
pam.module_assert
pam.order_assert
pam.pwhistory
pam.restore
pam.service_line
pam.stack_facts
pam.succeed_if
pam.validate
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
ssh.authorized_key_absent
ssh.config
ssh.fingerprint
ssh.host_keygen
ssh.keygen
ssh.known_hosts
ssh.public_key
sshd.config
sshd.validate
sudo.assert
sudo.can_run
sudo.list
sudo.rule
sudo.validate
sudoers.dropin
swap.absent
swap.present
swap.status
sysctl.assert
sysctl.dropin
sysctl.facts
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
timedatectl.ntp
timedatectl.status
timedatectl.timezone
transfer.download
transfer.rsync
transfer.sync
transfer.upload
udev.facts
udev.reload
udev.rule
udev.settle
udev.test
udev.trigger
udev.validate
ufw.delete
ufw.disable
ufw.enable
ufw.reset
ufw.rule
ufw.status
user.create
user.exists
user.facts
user.groups_assert
user.home_assert
user.lock
user.modify
user.remove
user.set_password
user.shell_assert
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
