# Changelog

## 0.1.0

Initial public release of Automax.

### Highlights

- Canonical builtin plugin DSL with audited plugin registry.
- YAML flow primitives: `if`, list-style `if`, `for`, `set`/`let`, `echo`, `fail`, `try`/`rescue`/`always`, `break`/`continue`, `assert`, `switch`/`case`/`default`, `retry`, `sleep`, `block`, and `noop`.
- Canonical plugin families for commands, filesystem, data, database, identity, network, OS/package management, security, storage, system/systemd, devices, and notifications.
- Operator preview, dry-run support, plugin audit guardrails, examples, runbooks, docs, and wiki aligned with the public DSL.

### Validation

- `python -m ruff check src tests scripts`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src pytest -q`
- `PYTHONPATH=src python -m automax.cli.cli plugins audit`
