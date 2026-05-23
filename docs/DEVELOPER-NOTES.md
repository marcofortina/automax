<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Developer notes

## Current architecture

```text
automax.cli
  -> automax.core.engine
      -> inventory / vars / secrets / templating
      -> plugin registry
      -> SSH session per step and target
      -> SQLite run state
```

## Commit style

Use short imperative messages, for example:

```text
bootstrap Automax SSH job automation engine
add filesystem plugins
add package manager plugins
```

## Public DSL policy

Automax exposes one canonical YAML DSL and one canonical builtin plugin namespace.
Compatibility aliases, ambiguous short names and ad-hoc validation utilities should
not be added to the public interface.
