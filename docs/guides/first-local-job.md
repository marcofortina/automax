<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# First local job

A local job is useful for validating the engine before using SSH.

Create `inventory.yaml`:

```yaml
servers:
  controller:
    host: 127.0.0.1
```

Create `job.yaml`:

```yaml
apiVersion: automax.io/v1
kind: Job
metadata:
  name: first-local-job
tasks:
  - id: smoke
    targets: all
    steps:
      - id: local
        substeps:
          - id: hello
            use: local.command
            with:
              command: "printf hello"
```

Validate and run:

```bash
automax validate --job job.yaml --inventory inventory.yaml
automax plan --job job.yaml --inventory inventory.yaml
automax run --job job.yaml --inventory inventory.yaml --state-dir .automax/runs
```

Inspect:

```bash
automax runs list --state-dir .automax/runs
automax runs show <run-id> --state-dir .automax/runs
```
