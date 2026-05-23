<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Future work

This page tracks product ideas that are intentionally not part of the current
implementation contract.

## Dynamic inventory providers

The current inventory source is YAML. Future inventory providers may load targets
from external systems at runtime, for example:

```text
inventory.file
inventory.command
inventory.http
```

This requires a stable provider contract before implementation so host discovery,
variables and failure handling remain predictable.

## Additional secret providers

The current secret providers are `env` and `file`. Future providers may include:

```text
Vault
AWS Secrets Manager
Azure Key Vault
Google Secret Manager
pass
1Password
```

These should be core secret providers, not job-action plugins, so secrets remain
resolved before templating and execution.

## Additional schema and output formats

Automax currently exports JSON Schema and supports JSON output for plan/run/resume
operator summaries. Future work may add additional formats without changing the
command shape, for example:

```bash
automax schema export --format=yaml
automax run --format=yaml ...
```
