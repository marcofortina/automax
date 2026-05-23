<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Installation

## Development install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
```

`.[dev]` installs test and documentation dependencies. This is the right mode for
contributors and CI-equivalent local validation.

## Runtime install

```bash
python -m pip install -e .
```

## Documentation-only install

```bash
python -m pip install -e '.[docs]'
```

Then build docs with:

```bash
NO_MKDOCS_2_WARNING=1 mkdocs build --strict
```

## Optional database drivers

SQLite is built into Python. Other database drivers are optional:

```bash
python -m pip install -e '.[postgres]'
python -m pip install -e '.[mysql]'
python -m pip install -e '.[oracle]'
python -m pip install -e '.[database]'
```

## Package smoke

```bash
scripts/package-smoke.sh
```

The package smoke verifies that Automax can be built, installed and invoked from
an installed environment.
