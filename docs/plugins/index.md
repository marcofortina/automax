# Builtin plugins

Only canonical plugin names are part of the public DSL. Compatibility aliases are
not exposed as public plugin names.

Current builtin plugins:

```text
archive.tar
archive.untar
archive.unzip
archive.zip
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
fs.symlink
fs.template
fs.write
local.command
pkg.install
pkg.query
pkg.remove
pkg.update_cache
pkg.upgrade
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
```

Use the CLI to inspect the installed plugin registry:

```bash
automax plugins list
```

External plugin modules can be added later through the registry mechanism without
changing the core execution engine.
