<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# CLI reference

## Validate

```bash
automax validate --job job.yaml --inventory inventory.yaml
```

Useful options:

```text
--vars PATH
--secrets PATH
--var KEY=VALUE
--tags TAGS
--skip-tags TAGS
```

## Plan

```bash
automax plan --job job.yaml --inventory inventory.yaml
```

Prints target, checkpoint, plugin and tags without executing the job.

## Run

```bash
automax run --job job.yaml --inventory inventory.yaml --state-dir .automax/runs
```

Restart from an explicit checkpoint in a new run:

```bash
automax run --job job.yaml --inventory inventory.yaml --from task.install
```

```bash
automax run --job job.yaml --inventory inventory.yaml --from task.install:step.packages
```

```bash
automax run --job job.yaml --inventory inventory.yaml --from task.install:step.packages:substep.nginx
```

## Resume

```bash
automax resume <run-id> --state-dir .automax/runs
```

Resume modes:

```bash
automax resume <run-id> --skip-successful
automax resume <run-id> --only-failed
automax resume <run-id> --from task.deploy:step.restart:substep.service
```

## Runs

```bash
automax runs list --state-dir .automax/runs
automax runs show <run-id> --state-dir .automax/runs
automax runs show <run-id> --failed
automax runs show <run-id> --server web01
automax runs show <run-id> --json
```

## Artifacts

```bash
automax artifacts list <run-id> --state-dir .automax/runs
automax artifacts path <run-id> --state-dir .automax/runs
```

## Plugins

```bash
automax plugins list
automax plugins describe fs.template
automax plugins describe fs.template --json
```

## Documentation helpers

```bash
automax docs generate-plugins --output docs/plugins/generated.md
```
