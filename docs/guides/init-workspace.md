<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Initialize an external automation workspace

Automax job definitions are external to the Python package. Use `automax init`
to create a clean starter workspace for jobs, inventory, variables, secrets and
templates:

```bash
automax init ./company-automation
```

Generated layout:

```text
company-automation/
  jobs/local-smoke.yaml
  inventory/local.yaml
  vars/local.yaml
  secrets/local.example.yaml
  templates/example.conf.j2
  README.md
```

Validate and run the starter job:

```bash
cd company-automation

automax validate --strict \
  --job jobs/local-smoke.yaml \
  --inventory inventory/local.yaml \
  --vars vars/local.yaml

automax run \
  --job jobs/local-smoke.yaml \
  --inventory inventory/local.yaml \
  --vars vars/local.yaml
```

`automax init` refuses to overwrite existing files. Use `--force` only when you
intentionally want to regenerate the skeleton:

```bash
automax init ./company-automation --force
```
