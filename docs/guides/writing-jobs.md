<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Writing jobs

A job should be explicit, small enough to inspect, and safe to resume.

## Recommended skeleton

```yaml
apiVersion: automax.io/v1
kind: Job
metadata:
  name: deploy-app
vars:
  app_name: myapp
targets: group:web
strategy:
  mode: rolling
  batch_size: 1
failurePolicy:
  onFailure: stop_host
  onUnreachable: stop_host
tasks:
  - id: prepare
    tags: [prepare]
    steps:
      - id: filesystem
        substeps:
          - id: create_dir
            use: fs.mkdir
            with:
              path: /opt/{{ vars.app_name }}
              mode: "0755"
              sudo: true
```

## Use canonical plugin names

Use names returned by:

```bash
automax plugins list
```

Inspect parameter metadata:

```bash
automax plugins describe fs.mkdir
```

## Keep secrets out of job files

Use `{{ secrets.name }}` references and resolve values from `env` or `file`
providers.

## Prefer idempotent macros

Prefer:

```yaml
use: fs.mkdir
```

over:

```yaml
use: remote.command
with:
  command: mkdir -p /opt/myapp
```

Builtin macros return `changed` where possible and are easier to describe,
document and test.

## Register outputs intentionally

```yaml
- id: app_version
  use: remote.command
  with:
    command: cat /opt/app/VERSION
  register:
    version: stdout.trim
```

Registered outputs are persisted in state and can be used by later substeps.
