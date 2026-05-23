<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Testing and CI

## Local validation

Install development dependencies:

```bash
python -m pip install -e '.[dev]'
```

Run the same local checks used by CI:

```bash
python -m compileall -q src tests scripts
python -m pytest -q
bash -n scripts/ssh-smoke.sh scripts/package-smoke.sh
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```

## Package smoke

```bash
scripts/package-smoke.sh
```

This validates build/install behavior from packaging metadata.

## SSH smoke

Use the extended SSH smoke when a real host is available:

```bash
AUTOMAX_SSH_HOST=web01.example.com \
AUTOMAX_SSH_USER=deploy \
AUTOMAX_SSH_KEY_FILE=$HOME/.ssh/id_ed25519 \
scripts/ssh-smoke.sh
```

Privileged package, systemd, user and group checks are opt-in. See
[Extended SSH smoke](../guides/ssh-smoke.md).

## GitHub Actions

The CI workflow runs Python tests across the supported Python matrix and builds
MkDocs strictly. The documentation workflow publishes the MkDocs site to GitHub
Pages.
