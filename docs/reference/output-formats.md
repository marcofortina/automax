<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Output formats

Operator-facing commands default to human-readable text output. Commands that
are useful in CI or automation can also emit JSON through `--format=json`.

## Plan JSON

```bash
automax plan \
  --job jobs/local-smoke.yaml \
  --inventory inventory/local.yaml \
  --format=json
```

The JSON plan includes the generated run id and every planned node:

```json
{
  "run_id": "20260523-120000-local-smoke-abc12345",
  "nodes": [
    {
      "target": "controller",
      "node_id": "task.smoke:step.local:substep.echo",
      "task_id": "smoke",
      "step_id": "local",
      "substep_id": "echo",
      "plugin": "local.command",
      "tags": []
    }
  ]
}
```

## Run JSON

```bash
automax run \
  --job jobs/local-smoke.yaml \
  --inventory inventory/local.yaml \
  --state-dir .automax/runs \
  --format=json
```

The JSON summary contains the run id, final status, target summaries, failed
nodes and resume commands:

```json
{
  "run_id": "20260523-120000-local-smoke-abc12345",
  "rc": 0,
  "status": "success",
  "summary": {
    "targets": 1,
    "nodes": 1,
    "success": 1,
    "failed": 0,
    "skipped": 0,
    "changed": 1,
    "artifacts": 0
  }
}
```

## Resume JSON

```bash
automax resume <run-id> --state-dir .automax/runs --only-failed --format=json
```

The JSON contract mirrors `run --format=json`, making it safe to consume from CI
pipelines and wrapper scripts.

## Text remains the default

The default output is still optimized for humans:

```bash
automax run --job job.yaml --inventory inventory.yaml
```

Use JSON only when another tool needs to parse the result.
