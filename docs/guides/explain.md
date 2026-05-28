<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Explain jobs before execution

`automax explain` resolves a job without creating run state or connecting to remote hosts. It shows task, step and substep expansion, selected targets, plugin names and resume checkpoints.

```bash
automax explain \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml
```

Example output:

```text
Job: deploy-app
Targets: web01, web02

Task deploy -> targets: web01, web02
  Step prepare -> opens a new SSH connection per target; targets: web01, web02
    Substep create_dir -> fs.dir.create; targets: web01, web02; checkpoint: task.deploy:step.prepare:substep.create_dir

Resume points:
  task.deploy:step.prepare:substep.create_dir
```

Use JSON output for automation:

```bash
automax explain \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --format=json
```
