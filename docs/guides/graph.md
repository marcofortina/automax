<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Graph job workflows

`automax graph` renders the resolved task/step/substep flow before execution.

Mermaid output is the default:

```bash
automax graph --job jobs/deploy.yaml --inventory inventory/prod.yaml
```

Other supported formats:

```bash
automax graph --job jobs/deploy.yaml --inventory inventory/prod.yaml --format=dot --output /tmp/job.dot
automax graph --job jobs/deploy.yaml --inventory inventory/prod.yaml --format=svg --output /tmp/job.svg
automax graph --job jobs/deploy.yaml --inventory inventory/prod.yaml --format=png --output /tmp/job.png
```

PNG output requires Graphviz `dot` in `PATH`. Mermaid, DOT and SVG output are generated directly by Automax.
