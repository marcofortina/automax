<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Contributing to Automax

Automax is being rebuilt around a clean SSH job automation engine. Keep changes
small, explicit and covered by tests.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

## Checks

```bash
python -m compileall -q src tests scripts
python -m pytest -q
bash -n scripts/ssh-smoke.sh
```

## Rules

- keep job, inventory, variables and secrets external to the source tree;
- expose only canonical plugin names in public docs and CLI output;
- add tests for every new plugin or engine behavior;
- prefer idempotent remote operations;
- do not reintroduce legacy plugin names, legacy managers or legacy utilities.
