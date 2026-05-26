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
automax plan --diff --job job.yaml --inventory inventory.yaml --format=json
```

Machine-readable output:

```bash
automax plan --job job.yaml --inventory inventory.yaml --format=json
```

## Run

```bash
automax run --job job.yaml --inventory inventory.yaml --state-dir .automax/runs
```

For sudo-enabled remote substeps on targets that require a sudo password, pass the controller-side environment variable name instead of configuring passwordless sudo on the target:

```bash
export AUTOMAX_SUDO_PASSWORD='...'
automax run --job job.yaml --inventory inventory.yaml --sudo-password-env AUTOMAX_SUDO_PASSWORD
```

Preview the selected run without creating run state. By default this prints a
compact per-task summary; add `--verbose` to show every per-target substep
preview.

```bash
automax run --check --job job.yaml --inventory inventory.yaml
automax run --check --verbose --job job.yaml --inventory inventory.yaml
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

## Capabilities

Inspect job-scoped remote tool requirements and install only the missing
dependency packages for the selected job and targets:

```bash
automax capabilities requirements --job job.yaml --inventory inventory.yaml
automax capabilities install --job job.yaml --inventory inventory.yaml --sudo-password-env AUTOMAX_SUDO_PASSWORD
```

`capabilities install` prints live check/plan/install status plus a compact
summary. Successful install command stdout/stderr is suppressed by default; add
`--verbose` when troubleshooting package-manager output. `--format=json` keeps
the full masked stdout/stderr payload for automation.

```bash
automax capabilities install --job job.yaml --inventory inventory.yaml --verbose
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
automax resume <run-id> --skip-successful --sudo-password-env AUTOMAX_SUDO_PASSWORD
```

## Runs

```bash
automax runs list --state-dir .automax/runs
automax runs show <run-id> --state-dir .automax/runs
automax runs show <run-id> --failed
automax runs show <run-id> --server web01
automax runs show <run-id> --json
```


## OS information

Detect operating-system release facts for inventory targets before capability
planning or dependency installation:

```bash
automax os info --inventory inventory.yaml
automax os info --inventory inventory.yaml --limit web --format=json
```

The output includes `ID`, `ID_LIKE`, pretty release name, version, codename,
normalized family (`debian`, `rhel` or `unknown`) and package manager.

## Inventory inspection

Show the inventory targets selected by a specific job:

```bash
automax inventory show --job job.yaml --inventory inventory.yaml
automax inventory show --job job.yaml --inventory inventory.yaml --limit web
automax inventory show --job job.yaml --inventory inventory.yaml --format=json
```

## Vars render

Render the final target-specific variable context for the selected job while
masking all secret values:

```bash
automax vars render --job job.yaml --inventory inventory.yaml --vars vars.yaml --secrets secrets.yaml
automax vars render --job job.yaml --inventory inventory.yaml --limit web01
automax vars render --job job.yaml --inventory inventory.yaml --format=json
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
# unavailable plugins are listed with an explicit reason instead of omitted
```

## SSH known_hosts scan

Scan SSH host keys for direct hosts or inventory-selected targets. The command
prints fingerprints so operators can verify them over a trusted channel before
using the generated known_hosts file:

```bash
automax ssh known-hosts scan --host web01.example.com
automax ssh known-hosts scan --inventory inventory/prod.yaml --limit web
automax ssh known-hosts scan --inventory inventory/prod.yaml --limit web --output ~/.ssh/automax_known_hosts
automax ssh known-hosts scan --host web01.example.com --format=json
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
