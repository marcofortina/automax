<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Automax

Automax is a Python, YAML-driven SSH automation engine for running resumable
job/task/step/substep workflows against remote systems.

Operational definitions are external to the Python sources:

- job YAML
- inventory YAML
- variables YAML
- secrets YAML
- optional external plugins


## Documentation site

The GitHub Pages site is the full public manual, not just a README mirror. It
includes quickstarts, concepts, guides, CLI reference, security notes, state and
resume documentation, artifacts and the generated builtin plugin reference.

Build it locally with:

```bash
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```

Start from `docs/index.md` or browse the published site configured in
`mkdocs.yml`.

## Core model

```text
Job
  Task[]
    Step[]
      Substep[]
```

A step opens one fresh SSH connection per target and reuses it for all its
substeps. Runtime context is not kept in a shell session: values are passed
through the Automax context, registered outputs and state store.

## Install

```bash
pip install -e .
```

Optional database drivers:

```bash
pip install -e '.[postgres]'
pip install -e '.[mysql]'
pip install -e '.[oracle]'
pip install -e '.[database]'
```

## Quick smoke

Install development extras before running the test suite. Installing only
`.[docs]` is enough for MkDocs, but it intentionally does not install `pytest`.

```bash
python -m pip install -e '.[dev]'
python -m compileall -q src tests scripts
python -m pytest -q
```

```bash
python -m automax validate \
  --job examples/next/jobs/local-smoke.yaml \
  --inventory examples/next/inventory/local.yaml
```

For a local-only plan:

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

Inspect an existing run:

```bash
automax runs show <run-id> --state-dir /var/lib/automax/runs
automax runs show <run-id> --state-dir /var/lib/automax/runs --failed
automax runs show <run-id> --state-dir /var/lib/automax/runs --server web01
```

Resume a failed run:

```bash
automax resume <run-id> --state-dir /var/lib/automax/runs
```

Resume from an explicit checkpoint:

```bash
automax resume <run-id> \
  --state-dir /var/lib/automax/runs \
  --from task.install:step.packages:substep.install_nginx
```

Task-level and step-level restart points are also accepted:

```bash
automax run --job job.yaml --inventory inventory.yaml --from task.install
automax run --job job.yaml --inventory inventory.yaml --from task.install:step.packages
```

## External files

Job, inventory, variable and secret files can live anywhere. They do not need to
be inside this repository.

```text
--job        /path/to/job.yaml
--inventory  /path/to/inventory.yaml
--vars       /path/to/vars.yaml
--secrets    /path/to/secrets.yaml
--state-dir  /path/to/run-state
```

## Builtin plugins

The public DSL exposes canonical plugin names only. Run:

```bash
automax plugins list
```

Current categories:

```text
commands:      local.command, remote.command
filesystem:    fs.*
archive:       archive.*
packages:      pkg.*
systemd:       systemctl.*
users/groups:  user.*, group.*
processes:     process.*
transfer:      transfer.*
http/api:      http.*
wait/assert:   wait.*, assert.*
database:      db.sqlite.query, db.postgres.query, db.mysql.query, db.oracle.query
```

See `docs/plugins/` for detailed examples of every builtin macro.

## Variables and secrets

Variables are external and can be overridden by CLI:

```bash
automax run --job job.yaml --inventory inventory.yaml --vars vars.yaml --var app_version=2.1.0
```

Secrets currently support only `env` and `file`, but the provider interface is
pluggable.

```yaml
secrets:
  ssh_user:
    provider: env
    name: AUTOMAX_SSH_USER

  ssh_key_file:
    provider: file
    path: ~/.ssh/id_ed25519.path
```

## Strategy, tags and failure policy

Strategies are scoped at job/task/step level:

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

Tags are filtered from the CLI:

```bash
automax run --job job.yaml --inventory inventory.yaml --tags install --skip-tags dangerous
```

Failure policy is declarative:

```yaml
failurePolicy:
  onFailure: stop_job      # stop_job, stop_task, stop_host, continue
  onUnreachable: stop_host
  maxFailedHosts: 1
```

## State store

Each run gets a generated `run-id`. The state store is local SQLite by default:

```text
.automax/runs/<run-id>/state.sqlite
```

It records run paths, checkpoints, target statuses, outputs and events. This is
required for audit and restart from task/step/substep.

## SSH smoke

Run the extended real SSH smoke against an operator-provided host:

```bash
AUTOMAX_SSH_HOST=192.0.2.10 \
AUTOMAX_SSH_USER=deploy \
AUTOMAX_SSH_KEY_FILE=~/.ssh/id_ed25519 \
AUTOMAX_SSH_HOST_KEY_POLICY=reject \
./scripts/ssh-smoke.sh
```

The default smoke is non-destructive and covers remote commands, filesystem,
archive, transfer, wait/assert and artifact capture. Optional package manager,
systemd and user/group/process checks are enabled with explicit environment
variables. See `docs/guides/ssh-smoke.md`.

External plugins can be loaded with:

```bash
automax run --job job.yaml --inventory inventory.yaml --plugin-path /opt/automax/plugins
```

## Documentation site

Build the documentation locally:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[docs]'
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```

Alternatively, when the package is not installed in editable mode, install the
documentation requirements explicitly before running MkDocs:

```bash
python -m pip install -r requirements-docs.txt
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```

GitHub Pages publishing is handled by `.github/workflows/docs.yml`. Configure the
repository Pages source as **GitHub Actions**.

## Operator tooling

Create an external job workspace:

```bash
automax init ./company-automation
```

Validate job definitions strictly before running them:

```bash
automax validate --strict --job jobs/local-smoke.yaml --inventory inventory/local.yaml
```

Check the controller environment:

```bash
automax doctor
```

## Python compatibility guardrails

Automax supports Python 3.9 and newer. Development and CI run an explicit
compatibility guard to catch runtime-only Python 3.10+ constructs before they
reach the Python 3.9 matrix job:

```bash
python scripts/check-python39-compat.py
```
