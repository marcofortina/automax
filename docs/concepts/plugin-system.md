<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Plugin system

Automax plugins are named operations loaded through the plugin registry.

Only canonical names are public DSL names. For example:

```text
fs.template
systemctl.restart
db.sqlite.query
```

Aliases are intentionally not exposed by `automax plugins list`.

## Inspect plugins

```bash
automax plugins list
automax plugins describe fs.template
automax plugins describe fs.template --json
automax plugins audit
```

## Metadata

Every builtin plugin has structured metadata:

- name;
- category;
- description;
- required parameters;
- optional parameters;
- parameter types and defaults;
- result fields;
- examples;
- remote-session and dry-run flags.

The generated plugin reference is built from this metadata:

```bash
automax docs generate-plugins --output docs/plugins/generated.md
```

## External plugins

The core execution engine is independent from the builtin plugin set. Future
external plugins can be registered without changing job orchestration, state
storage or SSH connection handling.
