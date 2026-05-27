<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Validation modes

`automax validate` checks external job, inventory, variable and secret files
without executing any substep. Plugin parameter validation always rejects
missing required parameters, unknown parameters, wrong scalar/container types and
supported schema bounds before a run can touch a target.

```bash
automax validate \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --vars vars/prod.yaml \
  --secrets secrets/prod.yaml
```

## Strict validation

Strict validation rejects ambiguous or unsupported configuration before a run:

```bash
automax validate --strict \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml
```

Strict mode checks:

- unsupported keys at job, task, step and substep level;
- unsupported or ambiguous DSL keys at resolved plan scope;
- target and tag filtering still resolves to a non-empty execution plan.

Use strict validation in CI for operational repositories that store Automax jobs.
