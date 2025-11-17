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
- Installable package + programmatic API
- Offline step validation utility

---

## 📁 Project Structure

```
automax/
├── .github/
│   └── workflows/
│       ├── ci.yml           # Continuous Integration workflow (tests, lint, etc.)
│       └── publish.yml      # Automated publishing to PyPI
├── docs/                    # Documentation
│   ├── CONTRIBUTING.md
│   ├── database_odbc_examples.yaml
│   └── DEVELOPER-NOTES.md
├── examples/                # Example configurations and demo data
│   ├── config/
│   │   └── config.yaml      # Example configuration file
│   ├── .ssh/                # Demo SSH keys (for illustrative use only)
│   └── steps/               # Example step definitions
├── logs/                    # Runtime logs (ignored by Git)
├── src/                     # Source code directory
│   └── automax/             # Core package (installable as Python module)
│       ├── cli/             # Command Line Interface package
│       ├── core/            # Core logic: managers, validation, runtime components
│       │   ├── managers/    # Core managers (config, plugins, steps, validation)
│       │   └── utils/       # Common utilities and logging
│       ├── plugins/         # Extensible plugin system
│       ├── __main__.py      # Entry point for `python -m automax`
│       └── main.py          # Programmatic API entry point
├── tests/                   # Unit and integration test suite
│   ├── test_core/           # Tests for core components
│   ├── test_plugins/        # Tests for plugins
│   └── test_steps/          # Tests for step logic
├── utils/                   # Developer utilities and scripts
├── pyproject.toml           # Modern build system configuration (PEP 621)
├── LICENSE.md               # License information
├── README.md                # Project overview and usage
├── requirements.txt         # Development dependencies
└── setup.py                 # Setup script (entry for setuptools)
```

---

## ⚙️ Installation

```bash
pip install .
# Or
python setup.py install
```

---

## ⚙️ CLI Usage

Automax provides a modern command-line interface:

### List available plugins
```bash
automax plugins list
```

### List available steps
```bash
automax list-steps --config examples/config/config.yaml
```

### Validate configuration file
```bash
automax validate --config examples/config/config.yaml
```

### Execute steps
```bash
automax run --config examples/config/config.yaml --steps 1,2
```

### Execute specific sub-steps
```bash
# Execute step 1 with all sub-steps, step 2 with all sub-steps, and only sub-step 8 of step 4
automax run --config examples/config/config.yaml --steps 1,2,4:8

# Execute only sub-step 3 of step 1 and sub-step 5 of step 2
automax run --config examples/config/config.yaml --steps 1:3,2:5
```

### Execute steps with variables
```bash
automax run --config examples/config/config.yaml --steps 1 --var timeout=10
```

### Dry-run execution
```bash
automax run --config examples/config/config.yaml --steps 1,2 --dry-run
```

### Help
```bash
automax --help
```

### Version
```bash
automax --version
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

## 💻 Development: Running without installation

During development (without 'pip install .'):
```bash
# Option 1: Python module
python -m automax list-steps --config examples/config/config.yaml

# Option 2: Direct script
python src/automax/cli/cli.py list-steps --config examples/config/config.yaml
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
export PYTHONPATH=$(pwd)/src
pytest -v
```

---

## 🧾 License

This project is distributed under a Modified MIT License (Non-Commercial Use).

You are free to use, copy, modify, and distribute the software for non-commercial purposes under the terms of the MIT License.

Commercial use — including integration into products, services, or projects that generate revenue — requires a separate commercial license.
