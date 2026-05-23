<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Quickstart

This quickstart uses only files already present in the repository and does not
require a remote server.

## 1. Create a virtual environment

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
```

## 2. Validate the example job

```bash
automax validate \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml
```

Validation checks the YAML shape, inventory resolution, plugin names and plugin
parameters before a run starts.

## 3. Preview the execution plan

```bash
automax plan \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml
```

Typical output:

```text
controller task.smoke:step.local:substep.echo plugin=local.command tags=-
```

## 4. Run the job

```bash
automax run \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml \
  --state-dir .automax/runs
```

The run prints an operator summary and the generated run id.

```text
Automax run completed
Run ID: 20260523-101530-local-smoke-a1b2c3d4
Status: success
State: .automax/runs/20260523-101530-local-smoke-a1b2c3d4
```

## 5. Inspect the run

```bash
automax runs list --state-dir .automax/runs
automax runs show <run-id> --state-dir .automax/runs
```

## 6. Inspect plugins

```bash
automax plugins list
automax plugins describe fs.template
```

## 7. Build the documentation

```bash
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```

For the full operator path against a remote host, continue with
[First SSH job](guides/first-ssh-job.md).
