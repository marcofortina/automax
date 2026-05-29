<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Execution model

Automax uses a fixed hierarchy:

```text
Job
  Task[]
    Step[]
      Substep[]
```

## Job

A job is the top-level YAML file. It declares metadata, default targets,
strategy, failure policy, variables and tasks.

## Task

A task groups related work. Examples:

- install packages;
- render configuration;
- restart services;
- validate health checks.

## Step

A step is the SSH connection boundary. For every resolved target, Automax opens a
new SSH connection for that step and runs all matching substeps through it.

## Substep

A substep calls one plugin:

```yaml
- id: install_nginx
  use: os.package.install
  with:
    name: nginx
    sudo: true
```

Substeps can register outputs for later use:

```yaml
- id: read_version
  use: remote.command
  with:
    command: cat /opt/app/VERSION
  register:
    app_version: stdout.trim
```

## Strategies

Supported strategies are:

```yaml
strategy:
  mode: serial
```

```yaml
strategy:
  mode: parallel
  max_parallel: 5
```

```yaml
strategy:
  mode: rolling
  batch_size: 2
  pause_between_batches: 10
```

## Failure policy

```yaml
failurePolicy:
  onFailure: stop_job
  onUnreachable: stop_host
  maxFailedHosts: 1
```

Supported failure decisions are `stop_job`, `stop_task`, `stop_host` and
`continue`.
