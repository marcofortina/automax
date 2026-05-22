<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Publishing documentation

Automax documentation is built with MkDocs and published to GitHub Pages from the
`docs/` tree and `mkdocs.yml`.

## Local preview

Install documentation dependencies:

```bash
pip install -e '.[docs]'
```

Serve locally:

```bash
mkdocs serve
```

Strict build:

```bash
mkdocs build --strict
```

The strict build is the same validation used by CI and the GitHub Pages workflow.

## GitHub Pages workflow

The `.github/workflows/docs.yml` workflow builds the documentation on pushes to
`master` or `main` when documentation, MkDocs configuration or Python API sources
change.

Required repository settings:

```text
Settings -> Pages -> Source: GitHub Actions
```

The published site URL is configured in `mkdocs.yml` as:

```text
https://marcofortina.github.io/automax/
```

## What belongs in docs

Keep operational documentation under `docs/`:

```text
docs/guides/      task-oriented guides
docs/reference/   stable DSL/API/reference material
docs/plugins/     builtin plugin manuals and examples
```

Every new builtin plugin should update `docs/plugins/` and should be covered by
examples that can be validated by `automax validate` or exercised by tests.
