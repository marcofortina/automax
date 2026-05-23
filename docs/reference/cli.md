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

Check-mode preview for the selected job:

```bash
automax plan --check --job job.yaml --inventory inventory.yaml
```

File diff preview for supported file-oriented plugins:

```bash
automax plan --diff --job job.yaml --inventory inventory.yaml
```

Machine-readable output:

```bash
automax plan --job job.yaml --inventory inventory.yaml --format=json
```

## Run

```bash
automax run --job job.yaml --inventory inventory.yaml --state-dir .automax/runs
```

Preview the selected run without creating run state:

```bash
automax run --check --job job.yaml --inventory inventory.yaml
```

Machine-readable final summary:

```bash
automax run --job job.yaml --inventory inventory.yaml --format=json
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

## Inventory inspection

Show the inventory targets selected by a specific job:

```bash
automax inventory show --job job.yaml --inventory inventory.yaml
automax inventory show --job job.yaml --inventory inventory.yaml --limit web
automax inventory show --job job.yaml --inventory inventory.yaml --format=json
```

## Secrets check

Check secret providers referenced by the selected job without printing values:

```bash
automax secrets check --job job.yaml --inventory inventory.yaml --secrets secrets.yaml
automax secrets check --job job.yaml --inventory inventory.yaml --secrets secrets.yaml --all
automax secrets check --job job.yaml --inventory inventory.yaml --secrets secrets.yaml --format=json
```

## Manual commands

Render copy/pasteable commands for selected substeps when a failed operation must
be reproduced manually before restarting from a checkpoint:

```bash
automax commands render --job job.yaml --inventory inventory.yaml
automax commands render --job job.yaml --inventory inventory.yaml --limit web01 --tags install
automax commands render --job job.yaml --inventory inventory.yaml --format=json
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

## Schema export

```bash
automax schema export --kind job --format=json --output automax-job.schema.json
automax schema export --kind inventory --format=json
```

## Documentation helpers

```bash
automax docs generate-plugins --output docs/plugins/generated.md
```

## Explain

Inspect a resolved job without creating run state:

```bash
automax explain --job jobs/deploy.yaml --inventory inventory/prod.yaml
automax explain --job jobs/deploy.yaml --inventory inventory/prod.yaml --format=json
```

## Graph

Render a resolved job graph:

```bash
automax graph --job jobs/deploy.yaml --inventory inventory/prod.yaml --format=mermaid
automax graph --job jobs/deploy.yaml --inventory inventory/prod.yaml --format=svg --output /tmp/job.svg
automax graph --job jobs/deploy.yaml --inventory inventory/prod.yaml --format=png --output /tmp/job.png
```

## Runbook export

Export a Markdown runbook from a resolved job:

```bash
automax runbook export --job jobs/deploy.yaml --inventory inventory/prod.yaml --output /tmp/runbook.md
```

## Run locking

Protect job and target concurrency with file-based locks:

```bash
automax run --job jobs/deploy.yaml --inventory inventory/prod.yaml --lock
automax resume <run-id> --lock --skip-successful
```

## Retry policies

Retry policies are declared in job YAML, not as CLI flags. They can be inherited
from job, task or step level and overridden on a substep:

```yaml
retry:
  attempts: 3
  delay: 2
  backoff: exponential
  max_delay: 10
```

Text output prints `[RETRY]` lines for visible retry attempts before the final
node result.
