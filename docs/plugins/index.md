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
archive.compress
archive.decompress
archive.tar
archive.untar
archive.unzip
archive.zip
assert.disk
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
network.connectivity.port_wait
network.dns.check
network.dns.config
network.dns.facts
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
platform.facts
plugin.requirements
process.assert_absent
process.assert_count
process.kill
process.signal
process.wait
remote.command
security.apparmor.complain
security.apparmor.disable
security.apparmor.enforce
security.apparmor.profile
security.apparmor.profile_check
security.apparmor.reload
security.apparmor.status
security.apparmor.validate
security.audit.backlog_check
security.audit.reload
security.audit.rule
security.audit.rules.facts
security.audit.search
security.audit.status
security.audit.syscall
security.audit.watch
security.authselect.check
security.authselect.profile
security.pam.access
security.pam.backup
security.pam.faillock
security.pam.include_check
security.pam.limits
security.pam.module_check
security.pam.order_check
security.pam.pwhistory
security.pam.restore
security.pam.service_line
security.pam.stack.facts
security.pam.succeed_if
security.pam.validate
security.password.policy
security.pki.cert.chain_check
security.pki.cert.expiry_check
security.pki.cert.expiry_report
security.pki.cert.fingerprint
security.pki.cert.install_keypair
security.pki.cert.issuer_check
security.pki.cert.key_match_check
security.pki.cert.san_check
security.pki.cert.self_signed
security.pki.cert.subject_check
security.pki.csr.generate
security.pki.key.permissions
security.pki.trust.install_bundle
security.pki.trust.install_ca
security.secret.redact_check
security.secret.scan_output
security.secret.scan_preview
security.selinux.boolean
security.selinux.context
security.selinux.fcontext
security.selinux.mode
security.selinux.port
security.selinux.restorecon
security.ssh.authorized_key.add
security.ssh.authorized_key.remove
security.ssh.config
security.ssh.fingerprint
security.ssh.host_keygen
security.ssh.keygen
security.ssh.known_hosts
security.ssh.public_key
security.sshd.config
security.sshd.validate
security.sudo.can_run
security.sudo.check
security.sudo.dropin
security.sudo.list
security.sudo.rule
security.sudo.validate
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
