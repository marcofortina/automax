<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# State store and resume

Every `automax run` creates or reuses a `run-id`. The `run-id` identifies one
execution attempt and is stored in a local SQLite state store by default:

```text
.automax/runs/<run-id>/state.sqlite
```

A different directory can be selected with `--state-dir`:

```bash
automax run \
  --job /srv/automax/jobs/deploy.yaml \
  --inventory /srv/automax/inventory/prod.yaml \
  --state-dir /var/lib/automax/runs
```

The state store records:

```text
job/inventory/vars/secrets paths
run status
node checkpoints
target status
plugin result data
events
registered outputs
```

## Listing runs

```bash
automax runs list --state-dir /var/lib/automax/runs
```

## Inspecting one run

```bash
automax runs show <run-id> --state-dir /var/lib/automax/runs
```

The command prints run metadata, aggregate node counts, per-target status, failed
checkpoints and ready-to-copy resume commands. Narrow the node table when needed:

```bash
automax runs show <run-id> --state-dir /var/lib/automax/runs --failed
automax runs show <run-id> --state-dir /var/lib/automax/runs --server web01
automax runs show <run-id> --state-dir /var/lib/automax/runs --json
```

A failed run also prints the same resume hints at the end of `automax run`, so an
operator can retry without opening the SQLite state manually.

## Resume from first failed node

```bash
automax resume <run-id> --state-dir /var/lib/automax/runs
```

## Resume from an explicit node

```bash
automax resume <run-id> \
  --state-dir /var/lib/automax/runs \
  --from task.install:step.packages:substep.install_nginx
```

Task-level and step-level checkpoints are accepted:

```text
task.install
task.install:step.packages
task.install:step.packages:substep.install_nginx
```

`resume` uses the original job, inventory, vars and secrets paths saved in the
state store. CLI variable overrides can still be supplied with `--var`.
