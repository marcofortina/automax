<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Artifacts

Artifacts are files captured under the run state directory for later inspection.
They are useful when a substep produces command output, diagnostics or structured
result data that should be kept separate from the SQLite checkpoint database.

Declare artifacts on a substep:

```yaml
- id: collect_version
  use: command.remote.run
  with:
    command: "myapp --version"
  artifacts:
    stdout: version.txt
    stderr: version.err
```

Supported artifact sources are:

- `stdout`: plugin standard output.
- `stderr`: plugin standard error.
- `data`: plugin structured result data as JSON.

Artifact names are relative paths below the node artifact directory. Absolute
paths and `..` path traversal are rejected.

```bash
automax artifacts list <run-id>
automax artifacts path <run-id>
```

Example visual layout:

```text
.automax/runs/20260523-demo/artifacts/
  web01/
    task.deploy_step.check_substep.version/
      version.txt
      version.err
```

Secret values resolved by Automax are masked before artifact content is written.
