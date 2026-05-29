<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Automax

Automax is a Python, YAML-driven SSH automation engine for operators who need
repeatable infrastructure jobs without embedding operational data inside the
application source tree.

It runs external job definitions against external inventories, stores every run
in a resumable state directory, and exposes automation through small builtin or
external plugins.

```text
Job
  Task[]
    Step[]
      Substep[]
```

## Why Automax

Automax is built around a few strict choices:

- **External operations**: jobs, inventories, variables and secrets are passed by
  path from the CLI.
- **SSH-first execution**: a step opens one fresh SSH connection per target and
  runs all matching substeps through that connection.
- **Resumable runs**: every execution gets a run id, SQLite state, failed-node
  tracking, artifacts and ready-to-copy resume commands.
- **Explicit plugins**: builtin plugin names are canonical and inspectable with
  `automax plugins list` and `automax plugins describe`.
- **Security-conscious defaults**: SSH host keys are rejected by default unless a
  lab inventory explicitly opts into insecure behavior.

## Start here

For a complete first run, use the [Quickstart](quickstart.md).

For installation and local development setup, use
[Installation](guides/installation.md).

For a first real SSH job against a remote host, use
[First SSH job](guides/first-ssh-job.md).

## What the public documentation covers

| Area | Page |
|---|---|
| Install and validate the tool | [Installation](guides/installation.md) |
| Run the first local smoke job | [Quickstart](quickstart.md) |
| Write job YAML | [Writing jobs](guides/writing-jobs.md) |
| Understand task/step/substep execution | [Execution model](concepts/execution-model.md) |
| Configure inventory, vars and secrets | [Inventory, variables and secrets](reference/inventory-vars-secrets.md) |
| Resume failed jobs | [State store and resume](reference/state-and-resume.md) |
| Inspect job scope, secrets, check-mode, diffs and manual recovery commands | [Job Inspection and Recovery](guides/job-inspection-and-recovery.md) |
| Inspect captured files and outputs | [Artifacts](reference/artifacts.md) |
| Inspect every CLI command | [CLI reference](reference/cli.md) |
| Review SSH and secret handling | [Security reference](reference/security.md) |
| Browse builtin plugins | [Builtin plugins](plugins/index.md) |
| Validate a real SSH runtime | [Extended SSH smoke](guides/ssh-smoke.md) |

## Minimal local smoke

```bash
python -m automax validate \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml

python -m automax run \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml
```

Inspect the run:

```bash
automax runs list
automax runs show <run-id>
```

## Plugin discovery

```bash
automax plugins list
automax plugins describe fs.file.template
automax docs generate-plugins --output docs/plugins/generated.md
```

The generated reference is published under
[Generated plugin reference](plugins/generated.md).
