<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Development tooling

Install development dependencies with:

```bash
python -m pip install -e '.[dev]'
```

Automax uses Ruff for Python linting and formatting checks. The CI lint gate is:

```bash
python -m ruff check src tests scripts
```

## Pre-commit

Install local hooks with:

```bash
pre-commit install
```

Run all hooks manually with:

```bash
pre-commit run --all-files
```

The hook set covers Ruff, YAML/TOML syntax checks, trailing whitespace and
end-of-file normalization.

## Compatibility checks

Before pushing, run:

```bash
python -m compileall -q src tests scripts
python scripts/check-python39-compat.py
python -m ruff check src tests scripts
python -m pytest -q
bash -n scripts/ssh-smoke.sh scripts/package-smoke.sh
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```
