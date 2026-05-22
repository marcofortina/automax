# Automax

Automax is a Python, YAML-driven automation engine for running job/task/step/substep workflows against remote systems over SSH.

This branch is the clean next implementation. Operational definitions are external to the Python sources:

- job YAML
- inventory YAML
- variables YAML
- secrets YAML
- optional external plugins

## Core model

```text
Job
  Task[]
    Step[]
      Substep[]
```

A step opens one fresh SSH connection per target and reuses it for all its substeps. Runtime context is not kept in a shell session: values are passed through the Automax context, outputs and state store.

## Quick smoke

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

## Job YAML

```yaml
apiVersion: automax.io/v1
kind: Job
metadata:
  name: deploy-app
vars:
  app_name: demo
strategy:
  mode: rolling
  batch_size: 2
failurePolicy:
  onFailure: stop_job
  onUnreachable: stop_host
tasks:
  - id: install
    targets: group:web
    tags: [install]
    steps:
      - id: packages
        tags: [packages]
        substeps:
          - id: check_user
            use: remote.command
            with:
              command: whoami
            register:
              remote_user: stdout.trim

          - id: make_dir
            use: fs.mkdir
            with:
              path: "/opt/{{ vars.app_name }}"
              owner: "{{ outputs.remote_user }}"
              mode: "0755"
```

## Inventory YAML

```yaml
servers:
  web01:
    host: 10.0.0.11
    groups: [web, production]
    vars:
      role: frontend
    ssh:
      user: "{{ secrets.ssh_user }}"
      key_file: "{{ secrets.ssh_key_file }}"
      known_hosts: ~/.ssh/known_hosts
      missing_host_key_policy: reject
```

Selectors accepted by `targets`, `--limit` and `--exclude`:

```text
all
server:web01
web01
group:web
web
```

## Variables and secrets

Variables are external and can be overridden by CLI:

```bash
automax run --job job.yaml --inventory inventory.yaml --vars vars.yaml --var app_version=2.1.0
```

Secrets currently support only `env` and `file`, but the provider interface is pluggable.

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

## Builtin plugins

Current implementation includes:

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

Builtin plugin names are intentionally canonical only. The YAML DSL should use the names listed above; legacy names and short aliases are not registered by default.

Run the real SSH smoke against an operator-provided host:

```bash
AUTOMAX_SSH_HOST=192.0.2.10 \
AUTOMAX_SSH_USER=deploy \
AUTOMAX_SSH_KEY_FILE=~/.ssh/id_ed25519 \
AUTOMAX_SSH_HOST_KEY_POLICY=reject \
./scripts/ssh-smoke.sh
```

External plugins can be loaded with:

```bash
automax run --job job.yaml --inventory inventory.yaml --plugin-path /opt/automax/plugins
```

## State store

Each run gets a generated `run-id`. The state store is local SQLite by default:

```text
.automax/runs/<run-id>/state.sqlite
```

It records run paths, checkpoints, target statuses, outputs and events. This is required for audit and restart from task/step/substep.

### Archive and systemd examples

Archive plugins are remote SSH macros around standard `tar`, `zip` and `unzip`
commands. Use `creates` when extraction or packaging should be idempotent.

```yaml
- id: pack_release
  use: archive.tar
  with:
    source: /opt/myapp
    dest: /tmp/myapp.tar.gz
    compression: gzip
    excludes:
      - "*.tmp"

- id: unpack_release
  use: archive.untar
  with:
    archive: /tmp/myapp.tar.gz
    dest: /opt/myapp
    strip_components: 1
    creates: /opt/myapp/bin/myapp
```

Systemd plugins run remotely through SSH. Set `sudo: true` when the remote user
has passwordless sudo for service management.

```yaml
- id: reload_systemd
  use: systemctl.daemon_reload
  with:
    sudo: true

- id: restart_service
  use: systemctl.restart
  with:
    service: myapp.service
    sudo: true
```
