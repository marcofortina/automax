<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Creating plugins

Automax plugins are small execution units loaded by the plugin registry.

A plugin should keep business logic outside the engine and expose one canonical
DSL name, for example `fs.dir.create` or `systemctl.restart`.

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
fs.file.template
pkg.install
systemctl.enable
transfer.upload
```

Avoid shortened or ambiguous names. Public DSL names should stay canonical, explicit and stable.

## Design rules

- validate required parameters before executing anything;
- prefer idempotent behavior when possible;
- never hide unsafe behavior behind defaults;
- return machine-readable outputs for `register:` mappings;
- keep compatibility aliases out of public docs and CLI output unless they are explicitly part of a documented extension contract.

## Inspecting plugin metadata

Use `automax plugins describe` to inspect a builtin or externally loaded plugin:

```bash
automax plugins describe fs.file.template
automax plugins audit --plugin-path ./plugins
```

The command prints the canonical name, description, required parameters, optional
parameters and whether the plugin opens a remote SSH session. External plugins loaded
with `--plugin-path` are described through the same registry contract.
