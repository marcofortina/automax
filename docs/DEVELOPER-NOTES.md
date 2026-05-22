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

## Cleanup policy

The old Automax DSL, old plugin names and old validation utilities must not come
back unless they are intentionally redesigned for the new engine.
