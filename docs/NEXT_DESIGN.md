# Automax Next Design

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

## Execution model

A step opens one fresh SSH connection per target and reuses it for all its substeps.
The runtime context is kept by Automax, not by a long-lived remote shell. Plugins that
need step-local state can use the `ExecutionContext.step_state` mapping. For example,
`fs.cd` sets the current remote working directory and `remote.command` applies it to
subsequent commands in the same step.

## External operational files

Automax does not require job, inventory, variable or secret files to live inside the
Python source tree. The CLI receives them explicitly:

```bash
automax run \
  --job /srv/automax/jobs/deploy.yaml \
  --inventory /srv/automax/inventory/prod.yaml \
  --vars /srv/automax/vars/prod.yaml \
  --secrets /srv/automax/secrets/prod.yaml
```

## Secrets

The first implementation supports only `env` and `file` providers. The provider
interface remains pluggable so Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret
Manager or other backends can be added later without changing the job DSL.

## Strategy

Strategy can be declared at job, task or step level. More specific scopes override less
specific scopes.

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

Failure policy can be declared at job, task or step level. More specific scopes override
less specific scopes.

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

Current builtins:

```text
local.command
remote.command
fs.cd
fs.mkdir
fs.copy
fs.remove
fs.chown
fs.chmod
archive.tar
archive.untar
archive.zip
archive.unzip
systemctl.start
systemctl.stop
systemctl.restart
systemctl.daemon_reload
```

Builtin plugin names are canonical only: no legacy or short aliases are exposed by default. External plugins can still define aliases, but `automax plugins list` shows canonical names unless `--include-aliases` is requested.

External plugins can be loaded with `--plugin-path`.

## Remaining non-goals for this implementation

- Cloud secret providers.
- Central database state backend.
- Full Ansible-equivalent module coverage.

## Archive and systemd macros

Archive support is implemented as plugin macros instead of core engine logic:

```text
archive.tar
archive.untar
archive.zip
archive.unzip
```

Systemd support is also plugin-based:

```text
systemctl.start
systemctl.stop
systemctl.restart
systemctl.daemon_reload
```

These plugins execute through the step-scoped SSH connection, so they follow the
same restart, state, tag and failure policy behavior as every other substep.
