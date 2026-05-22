<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Automax

Automax is a Python, YAML-driven SSH automation engine for external job files,
external inventories and resumable infrastructure workflows.

It uses a strict execution model:

```text
Job
  Task[]
    Step[]
      Substep[]
```

Each step opens one fresh SSH connection per target host and reuses that
connection for all substeps in the step. Runtime context is carried by Automax
through variables, registered outputs, step-local state and the SQLite run state
store, not by relying on a persistent shell session.

## Install

Runtime dependencies are intentionally small:

```bash
pip install -e .
```

Database drivers are optional except SQLite, which is built into Python:

```bash
pip install -e '.[postgres]'
pip install -e '.[mysql]'
pip install -e '.[oracle]'
pip install -e '.[database]'
```

## Quick start

Validate a job:

```bash
python -m automax validate \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml
```

Show the execution plan:

```bash
python -m automax plan \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml
```

Run a job:

```bash
automax run \
  --job /srv/automax/jobs/deploy.yaml \
  --inventory /srv/automax/inventory/prod.yaml \
  --vars /srv/automax/vars/prod.yaml \
  --secrets /srv/automax/secrets/prod.yaml \
  --state-dir /var/lib/automax/runs
```

Resume a failed run:

```bash
automax resume <run-id> --state-dir /var/lib/automax/runs
```

Resume from a specific checkpoint:

```bash
automax resume <run-id> \
  --state-dir /var/lib/automax/runs \
  --from task.install:step.packages:substep.install_nginx
```

## External operational files

Automax does not require jobs, inventories, variables or secrets to live inside
this repository. They are passed explicitly to the CLI:

```text
--job        /path/to/job.yaml
--inventory  /path/to/inventory.yaml
--vars       /path/to/vars.yaml
--secrets    /path/to/secrets.yaml
--state-dir  /path/to/run-state
```

See the reference pages for the exact formats:

- [Job DSL](reference/job-dsl.md)
- [Inventory, variables and secrets](reference/inventory-vars-secrets.md)
- [State store and resume](reference/state-and-resume.md)

## Plugin manuals

Builtin plugin names are canonical only. The current builtins are documented by
category under [Builtin plugins](plugins/index.md):

- commands
- filesystem
- archive
- package manager
- systemctl
- users, groups and processes
- transfer
- HTTP/API
- wait/assert
- database

Use the CLI to inspect the registry installed in the current environment:

```bash
automax plugins list
```
