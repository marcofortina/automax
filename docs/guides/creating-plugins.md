# Creating plugins

Automax plugins are small execution units loaded by the plugin registry.

A plugin should keep business logic outside the engine and expose one canonical
DSL name, for example `fs.mkdir` or `systemctl.restart`.

## Contract

A plugin receives:

- rendered input parameters from the substep `with:` block;
- the current target server context;
- an optional SSH session when the plugin is remote;
- the runtime context and previously registered outputs.

A plugin returns a structured result with at least:

```text
ok
changed
failed
skipped
outputs
message
```

## Naming rules

Use canonical names only:

```text
category.action
```

Good examples:

```text
fs.template
pkg.install
systemctl.enable
transfer.upload
```

Avoid legacy, shortened or ambiguous names. Do not expose aliases as public DSL names unless there is a strong migration reason.

## Design rules

- validate required parameters before executing anything;
- prefer idempotent behavior when possible;
- never hide unsafe behavior behind defaults;
- return machine-readable outputs for `register:` mappings;
- keep aliases internal unless there is a strong migration reason.
