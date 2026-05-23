<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Export runbooks

`automax runbook export` turns a resolved job into a Markdown operator runbook. It does not execute the job and does not create run state.

```bash
automax runbook export \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --output /tmp/deploy-runbook.md
```

The runbook includes:

- selected targets;
- task, step and substep order;
- whether a step opens SSH connections;
- plugin names;
- resume checkpoints.

Use it for reviews, operational handovers and GitHub issue/PR attachments.
