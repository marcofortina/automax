<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Python compatibility

Automax supports Python 3.9 and newer. The GitHub Actions matrix keeps Python
3.9 in the required test set so runtime compatibility regressions are caught
before merge.

## Why there is an explicit guard

Some Python 3.10+ constructs still parse on Python 3.9 when they appear in
runtime expressions, but fail when executed. The common example is this pattern:

```python
isinstance(value, int | float)
```

That expression raises a `TypeError` on Python 3.9. The compatible form is:

```python
isinstance(value, (int, float))
```

## Local check

Run the compatibility guard with:

```bash
python scripts/check-python39-compat.py
```

The check scans `src/`, `tests/` and `scripts/` for unsafe runtime union usage in
`isinstance()` and `issubclass()` calls.

## CI behavior

The CI workflow runs both:

```bash
python -m compileall -q src tests scripts
python scripts/check-python39-compat.py
python -m pytest -q
```

The explicit guard complements, but does not replace, the Python 3.9 CI matrix.
