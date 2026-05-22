# Automax

Automax is a Python, YAML-driven SSH job automation engine.

It runs external job definitions against external inventories using a strict
`Job -> Task -> Step -> Substep` model. Source code and operational job files are
kept separate by design.

## Core model

```text
Job
  Task[]
    Step[]
      Substep[]
```

Each step opens a fresh SSH connection per target host and reuses that connection
for all substeps in the step. Runtime state is carried by Automax through context,
registered outputs and the run state store, not by relying on a persistent shell.

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

## Builtin plugins

See [Builtin plugins](plugins/index.md) for the current canonical plugin list.
