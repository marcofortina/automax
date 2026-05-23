<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Exported schemas

Automax can export machine-readable JSON Schema documents for operator-owned
YAML files. The command is intentionally format-aware so future formats can be
added without changing the command shape.

## Export job schema

```bash
automax schema export --kind job --format=json --output automax-job.schema.json
```

Without `--output`, the schema is written to stdout:

```bash
automax schema export --kind job --format=json
```

## Supported kinds

```text
job
inventory
vars
secrets
all
```

`all` produces a single JSON document containing all exported schemas under
named top-level properties.

## Current format

Only JSON is currently supported:

```bash
automax schema export --kind inventory --format=json --output inventory.schema.json
```

The inventory schema covers static inventories and dynamic `file`, `command` and
`http` provider wrappers. The secrets schema covers `env`, `file` and `command`
providers.

The explicit `--format=json` option is part of the public CLI contract. It keeps
the interface extensible for future formats such as YAML or OpenAPI-oriented
exports.

## Suggested use

The exported schema can be used by editors, pre-commit checks or CI pipelines to
validate the shape of job and inventory files before running Automax:

```bash
automax schema export --kind job --format=json --output /tmp/automax-job.schema.json
```

The exported schema defines the DSL structure. Plugin-specific parameter checks
remain owned by Automax and are validated with:

```bash
automax validate --strict --job job.yaml --inventory inventory.yaml
```
