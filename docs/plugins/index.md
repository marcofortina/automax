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
apparmor.profile
apparmor.reload
apparmor.status
archive.tar
archive.untar
archive.unzip
archive.zip
assert.command
assert.disk
assert.file
assert.path
assert.tcp
db.mysql.query
db.oracle.query
db.postgres.query
db.sqlite.query
firewalld.port
firewalld.reload
firewalld.rich_rule
firewalld.service
fs.cd
fs.chmod
fs.chown
fs.copy
fs.exists
fs.find
fs.line
fs.mkdir
fs.move
fs.read
fs.remove
fs.replace
fs.stat
fs.symlink.create
fs.symlink.remove
fs.template
fs.write
fstab.entry
group.create
group.exists
group.remove
http.assert
http.request
http.wait
kernel.module.load
kernel.module.persist
kernel.module.unload
local.command
mount.absent
mount.present
nftables.apply
nftables.validate
pkg.install
pkg.key.add
pkg.key.remove
pkg.query
pkg.remove
pkg.repo.add
pkg.repo.remove
pkg.update_cache
pkg.upgrade
process.kill
process.wait
remote.command
selinux.boolean
selinux.context
selinux.mode
selinux.restorecon
ssh.authorized_key
sudoers.dropin
sysctl.get
sysctl.persist
sysctl.reload
sysctl.set
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
transfer.download
transfer.sync
transfer.upload
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
