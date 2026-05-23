<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Inventory, variables and secrets

Automax keeps operational data outside the source tree. Jobs, inventories,
variables and secrets are passed by path from the CLI:

```bash
automax run \
  --job /srv/automax/jobs/deploy.yaml \
  --inventory /srv/automax/inventory/prod.yaml \
  --vars /srv/automax/vars/prod.yaml \
  --secrets /srv/automax/secrets/prod.yaml
```

## Inventory

Inventory can be static YAML or dynamic provider output. Static inventory defines target servers, groups, host variables and SSH connection data:

```yaml
servers:
  web01:
    host: 10.0.0.11
    port: 22
    groups: [web, production]
    vars:
      role: frontend
    ssh:
      user: "{{ secrets.ssh_user }}"
      key_file: "{{ secrets.ssh_key_file }}"
      known_hosts: ~/.ssh/known_hosts
      missing_host_key_policy: reject
```

Supported SSH fields are read into the target model or passed through the `ssh`
mapping for the SSH manager. Use `missing_host_key_policy: reject` for real
environments. Lab-only policies should be explicit in the inventory.

Dynamic inventory providers are also supported when the target list is generated
by another local tool or inventory service:

```yaml
inventory:
  provider: command
  command: ["./scripts/list-hosts.py", "--env", "prod"]
  format: yaml
  timeout: 30
```

Supported providers are `file`, `command` and `http`. See
[Dynamic inventory](../guides/dynamic-inventory.md) for provider-specific
examples and safety notes.

## Variable precedence

The current precedence is:

```text
CLI --var overrides
> job vars
> external vars file
```

Target variables are merged at execution time and override the global variable
view for that target:

```text
target.vars > merged global vars
```

Example variables file:

```yaml
vars:
  app_name: myapp
  version: 1.2.3
  environment: production
```

CLI overrides:

```bash
automax run --job job.yaml --inventory inventory.yaml --var version=1.2.4
```

## Secrets

Secrets currently support `env`, `file` and `command` providers. The secret
provider interface is intentionally pluggable so Vault, cloud secret managers or
other providers can be added later without changing job YAML semantics.

```yaml
secrets:
  ssh_user:
    provider: env
    name: AUTOMAX_SSH_USER

  ssh_key_file:
    provider: file
    path: ~/.ssh/automax-key-path

  deploy_token:
    provider: command
    command: ["pass", "show", "prod/automax/deploy-token"]
    timeout: 10
```

Shorthand forms are also supported:

```yaml
secrets:
  ssh_user:
    env: AUTOMAX_SSH_USER
  ssh_key_file:
    file: ~/.ssh/automax-key-path
  deploy_token:
    command: ["pass", "show", "prod/automax/deploy-token"]
```

A plain string is accepted as an already-resolved secret value, but this should be
reserved for local labs and examples. See [Command secrets](../guides/command-secrets.md)
for generic external command integration and shell-safety guidance.

## Template context

Rendered job values and plugin parameters can use:

```text
job
 task
 step
 substep
 server / target
 vars
 secrets
 outputs
 step_state
```

`fs.template` adds one extra namespace: `values`, taken from
`fs.template.with.values`.

## SSH security options

Automax defaults to conservative SSH behavior:

```yaml
servers:
  app01:
    host: app01.example.com
    ssh:
      user: deploy
      key_file: ~/.ssh/id_ed25519
      known_hosts: ~/.ssh/known_hosts
      missing_host_key_policy: reject
      allow_agent: false
      look_for_keys: false
      strict_key_permissions: true
```

`missing_host_key_policy: auto_add` is intentionally blocked unless the inventory
also sets `allow_insecure_host_key_policy: true`. Use that only for disposable lab
hosts, never for production.

Private key files are checked by default and must not be accessible by group or
other users. Use `chmod 600` on private keys instead of disabling the check.

Secrets resolved from `env` or `file` are masked before stdout, stderr, messages
and plugin result data are persisted to the SQLite run state.
