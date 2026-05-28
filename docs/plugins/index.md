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
assert.disk
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
backup.manifest
backup.prune
backup.restore
backup.restore_preview
backup.restore_verify
backup.rotate
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
capability.assert
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
fs.acl.check
fs.acl.get
fs.acl.restore
fs.acl.set
fs.attr.check
fs.attr.get
fs.attr.set
fs.bind_mount
fs.cd
fs.dir.create
fs.dir.exists
fs.dir.remove
fs.dir.wait
fs.disk_usage_assert
fs.file.create
fs.file.exists
fs.file.line
fs.file.read
fs.file.remove
fs.file.replace
fs.file.template
fs.file.wait
fs.file.write
fs.inode_usage_assert
fs.object.copy
fs.object.find
fs.object.move
fs.object.stat
fs.permission.mode
fs.permission.owner
fs.quota
fs.resize
fs.symlink.create
fs.symlink.exists
fs.symlink.remove
fs.symlink.wait
fstab.absent
fstab.assert
fstab.entry
fstab.validate
group.create
group.exists
group.member_absent
group.members
group.remove
hostname.set
hosts.entry
http.assert
http.request
http.wait
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
network.connectivity.port_check
network.dns
network.dns_assert
network.dns_facts
network.firewall.firewalld.forward_port
network.firewall.firewalld.icmp_block
network.firewall.firewalld.list
network.firewall.firewalld.masquerade
network.firewall.firewalld.port
network.firewall.firewalld.reload
network.firewall.firewalld.rich_rule
network.firewall.firewalld.service
network.firewall.firewalld.source
network.firewall.firewalld.status
network.firewall.firewalld.zone
network.firewall.iptables.chain
network.firewall.iptables.counter_assert
network.firewall.iptables.delete
network.firewall.iptables.exists_assert
network.firewall.iptables.list
network.firewall.iptables.policy
network.firewall.iptables.restore
network.firewall.iptables.rule
network.firewall.iptables.save
network.firewall.nftables.apply
network.firewall.nftables.export
network.firewall.nftables.list
network.firewall.nftables.rollback_file
network.firewall.nftables.ruleset_assert
network.firewall.nftables.validate
network.firewall.ufw.delete
network.firewall.ufw.disable
network.firewall.ufw.enable
network.firewall.ufw.reset
network.firewall.ufw.rule
network.firewall.ufw.status
network.link.bond
network.link.bridge
network.link.check
network.link.facts
network.link.interface
network.link.vlan
network.route.add
network.route.check
network.route.facts
network.route.remove
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
plugin.requirements
process.assert_absent
process.assert_count
process.kill
process.signal
process.wait
remote.command
secret.redact_assert
secret.scan_output
secret.scan_preview
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
tool.exists
tool.version_assert
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
