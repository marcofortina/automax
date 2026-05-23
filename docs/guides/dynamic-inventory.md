<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Dynamic inventory

Automax normally reads targets from a static YAML inventory passed with
`--inventory`. Dynamic inventory keeps the same external-file model, but the
inventory file can delegate host discovery to a provider.

Dynamic inventory is resolved before plan/run execution and after variables and
secrets are loaded, so provider definitions can use `{{ vars.* }}` and
`{{ secrets.* }}`.

## Static inventory

```yaml
servers:
  web01:
    host: 10.0.0.11
    groups: [web]
```

## File provider

Use `provider: file` when one inventory should include another generated file:

```yaml
inventory:
  provider: file
  path: generated/prod.yaml
```

Relative paths are resolved relative to the inventory wrapper file.

The referenced file must return a normal Automax inventory document:

```yaml
servers:
  web01:
    host: 10.0.0.11
    groups: [web]
```

## Command provider

Use `provider: command` when an internal script or CMDB client prints inventory
to stdout:

```yaml
inventory:
  provider: command
  command: ["./scripts/list-hosts.py", "--environment", "prod"]
  format: yaml
  timeout: 30
```

The command must exit with code `0` and print a mapping containing `servers`.
Both YAML and JSON payloads are accepted:

```json
{
  "servers": {
    "web01": {
      "host": "10.0.0.11",
      "groups": ["web"]
    }
  }
}
```

By default, string commands are split without a shell. Use list form whenever
possible:

```yaml
command: ["python3", "scripts/list-hosts.py", "--env", "prod"]
```

`shell: true` is supported only when explicitly requested:

```yaml
inventory:
  provider: command
  command: "./scripts/list-hosts.sh prod"
  shell: true
```

Do not use `shell: true` with untrusted variables.

## HTTP provider

Use `provider: http` when a CMDB or inventory API returns the inventory payload:

```yaml
inventory:
  provider: http
  url: "https://cmdb.example/api/automax/prod"
  headers:
    Authorization: "Bearer {{ secrets.cmdb_token }}"
  format: json
  timeout: 15
```

Only `GET` is currently supported. The response body must contain an Automax
inventory document.

## Validation

Dynamic inventories work with the same commands as static inventories:

```bash
automax validate --strict --job jobs/deploy.yaml --inventory inventory/prod.yaml
automax plan --job jobs/deploy.yaml --inventory inventory/prod.yaml
automax run --job jobs/deploy.yaml --inventory inventory/prod.yaml
```

Use `automax schema export --kind inventory --format=json` to export the schema
for static and dynamic inventory documents.
