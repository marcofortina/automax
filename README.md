# 🤖 Automax

[![CI](https://github.com/marcofortina/automax/actions/workflows/ci.yml/badge.svg)](https://github.com/marcofortina/automax/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.md)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)]()

**Automax** is a modular, YAML-driven automation framework for executing steps and sub-steps from CLI or Python code.

---

## 🧩 Features

- Step/sub-step in YAML
- CLI discovery dinamica
- Fail-fast, logging (file/console)
- Dry-run
- Config YAML (SSH, paths, logging, steps_dir)
- Validazione YAML/parametri
- Plugin estensibili (local cmd, SSH, HTTP, etc.)
- Retry, context output, hook pre/post
- Programmatic API
- Offline step validation utility

---

## 📁 Project Structure

```
automax/
├── automax/                 # Core package (installabile come modulo Python)
│   ├── __init__.py          # Package initializer
│   ├── __main__.py          # Entry point for `python -m automax`
│   ├── cli.py               # Command Line Interface
│   ├── main.py              # Programmatic API entry point
│   ├── core/                # Core logic: managers, validation, runtime components
│   └── plugins/             # Extensible plugin system
├── examples/                # Example configurations and demo data
│   ├── config/
│   │   └── config.yaml      # Example configuration file
│   ├── .ssh/                # Demo SSH keys (for illustrative use only)
│   └── steps/               # Example step definitions
├── tests/                   # Unit and integration test suite
│   ├── __init__.py          # Marks test suite as a package
│   ├── test_core/           # Tests for core components
│   ├── test_plugins/        # Tests for plugins
│   └── test_steps/          # Tests for step logic
├── utils/                   # Developer utilities and scripts (e.g., offline validation)
├── LICENSE.md               # License information
└── README.md                # Project overview and usage
```

---

## ⚙️ CLI Usage

⚠️ The CLI is not yet installable via pip.
To test commands locally, run Automax through the module interface (python -m automax).

### List steps
```bash
python -m automax --list --config examples/config/config.yaml
```

### Validate only
```bash
python -m automax 1 2 --validate-only --config examples/config/config.yaml
```

### Dry-run
```bash
python -m automax 1 2 --dry-run --config examples/config/config.yaml
```

### Execute steps
```bash
python -m automax 1 2 --config examples/config/config.yaml
```

### Help
```bash
python -m automax --help
```

---

## 🧩 Programmatic Usage

```python
from automax import run_automax

rc = run_automax(
    steps=["1", "2:1"],
    config_path="examples/config/config.yaml",
    dry_run=True,
)
print("Exit code:", rc)
```

---

## 🛠️ Offline Utilities

Automax provides standalone Python utilities for offline validation:

- **validate_step.py**: Validate a single step YAML file using config and plugin schemas.
- **validate_plugins.py**: Validate all plugins in the plugins directory.
- **check_step_deps.py**: Verify step dependencies and plugin references.
- **check_config.py**: Validate config YAML structure and required keys.
- **dry_run_validate.py**: Execute steps in dry-run mode programmatically.
- **lint_yaml.py**: Check YAML files for syntax errors.

---

## 🧩 Extending Steps

1. Copy `examples/steps/` to your project.
2. Add `stepX/` folder with:
   - `stepX.yaml` (required)
   - `stepX.py` (optional hooks)
3. Update your config.yaml:
   ```yaml
   steps_dir: "path/to/your/steps"
   ```

Example `stepX.yaml`:
```yaml
description: "My custom step"
substeps:
  - id: "1"
    description: "Run command"
    plugin: "run_local_command"
    params:
      command: "echo hello world"
```

---

## 🧪 Running Tests

```bash
export PYTHONPATH=$(pwd)
pytest -v
```

---

## 🧾 License

This project is distributed under a Modified MIT License (Non-Commercial Use).

You are free to use, copy, modify, and distribute the software for non-commercial purposes under the terms of the MIT License.

Commercial use — including integration into products, services, or projects that generate revenue — requires a separate commercial license.