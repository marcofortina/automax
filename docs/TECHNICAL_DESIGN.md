<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Automax Technical Design

## Goals

- Python implementation.
- External YAML definitions for jobs, inventories, variables and secrets.
- Modular plugin architecture.
- SSH-first execution model.
- Three-level job structure: task, step, substep.
- Step-scoped SSH connection reuse.
- State store for resume and audit.
- Serial, parallel and rolling execution strategies.
- Tag-based selection and skip filters.
- Declarative failure policy.
- Canonical builtin plugin names with no public compatibility aliases.

## Execution model

A step opens one fresh SSH connection per target and reuses it for all its
substeps. The runtime context is kept by Automax, not by a long-lived remote
shell. Plugins that need step-local state can use the `ExecutionContext.step_state`
mapping. For example, `fs.cd` sets the current remote working directory and
`remote.command` applies it to subsequent commands in the same step.

Targets can be scoped at job, task, step or substep level. When substeps in the
same step resolve to different target sets, Automax keeps one execution group per
step/target and runs only the matching substeps for that target.

## External operational files

Automax does not require job, inventory, variable or secret files to live inside
the Python source tree. The CLI receives them explicitly:

```bash
automax run \
  --job /srv/automax/jobs/deploy.yaml \
  --inventory /srv/automax/inventory/prod.yaml \
  --vars /srv/automax/vars/prod.yaml \
  --secrets /srv/automax/secrets/prod.yaml
```

## Secrets

The first implementation supports only `env` and `file` providers. The provider
interface remains pluggable so Vault, AWS Secrets Manager, Azure Key Vault, GCP
Secret Manager or other backends can be added later without changing the job DSL.

## Strategy

Strategy can be declared at job, task or step level. More specific scopes override
less specific scopes.

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

## Tags

Tags can be declared at job, task, step or substep level and are inherited as an
effective set for each substep.

```bash
automax run --job job.yaml --inventory inventory.yaml --tags deploy --skip-tags dangerous
```

## Failure policy

Failure policy can be declared at job, task or step level. More specific scopes
override less specific scopes.

```yaml
failurePolicy:
  onFailure: stop_job
  onUnreachable: stop_host
  maxFailedHosts: 1
```

Supported actions:

```text
stop_job
stop_task
stop_host
continue
```

## Builtin plugin scope

Current builtins are grouped into these categories:

```text
commands:      local.command, remote.command
filesystem:    fs.*
archive:       archive.*
packages:      pkg.*
system:       system.service.*, system.systemd.*, system.kernel.*, system.process.*, system.cron.*, system.journal.*, system.log.*
identity:      identity.user.*, identity.group.*
transfer:      transfer.*
http/api:      http.*
connectivity:   network.connectivity.*
storage:        storage.*
database:      db.*.query
```

Builtin plugin names are canonical only: no short or ambiguous compatibility aliases
are exposed by default. External plugins can still define aliases, but
`automax plugins list` shows canonical names unless `--include-aliases` is
requested.

External plugins can be loaded with `--plugin-path`.

## Remaining non-goals for this implementation

- Cloud secret providers.
- Central database state backend.
- Deploy-release orchestration macros with rollback semantics.
- Full Ansible-equivalent module coverage.

## Database design

SQLite is built in. PostgreSQL, MySQL and Oracle use optional Python extras. The
shared database plugin base owns statement validation, transaction flow and output
shaping so new database backends can be added as small driver-specific modules.
