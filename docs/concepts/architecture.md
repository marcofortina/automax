<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Architecture

Automax separates the installed engine from operational definitions.

```text
CLI
  -> YAML loader
  -> Inventory and variable resolver
  -> Secret resolver
  -> Plugin registry
  -> Execution engine
  -> SSH session manager
  -> SQLite state store
  -> Artifact store
```

## Engine responsibilities

The engine is responsible for deterministic orchestration:

- load external job, inventory, vars and secrets files;
- render templated parameters;
- expand targets at job, task, step and substep level;
- execute task/step/substep nodes;
- apply strategy, tags and failure policy;
- persist node results and run summaries;
- support resume from a failed run or explicit checkpoint.

## Plugin responsibilities

Plugins are intentionally small. A plugin validates its own parameters and
performs one operation, such as running a command, writing a file, installing a
package or querying a database.

Plugins do not own the global run state. They return a normalized result object
with status, change flag, stdout, stderr, message and structured data.

## SSH model

A step opens a new SSH connection per target. All substeps selected for that
target inside the step reuse that one connection.

State is not carried through an interactive shell. Context is carried explicitly
through Automax variables, registered outputs and the SQLite state store.

## Runtime state

The default state layout is:

```text
.automax/runs/<run-id>/
  state.sqlite
  artifacts/
```

Use `--state-dir` to move it to an operator-controlled location such as
`/var/lib/automax/runs`.
