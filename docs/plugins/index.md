# Builtin plugins

Only canonical plugin names are part of the public DSL. Compatibility aliases are
not exposed as public plugin names.

Use the CLI to inspect the installed plugin registry:

```bash
automax plugins list
```

Current builtin plugins:

```text
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
group.create
group.remove
http.assert
http.request
http.wait
local.command
pkg.install
pkg.query
pkg.remove
pkg.update_cache
pkg.upgrade
process.kill
process.wait
remote.command
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
user.create
user.modify
user.remove
wait.command
wait.file
wait.path
wait.process
wait.tcp
```

## Manuals by category

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

External plugin modules can be added through the registry mechanism without
changing the core execution engine.
