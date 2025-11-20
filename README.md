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
│   ├── workflows/           # CI/CD workflows
│   │   ├── ci.yml
│   │   ├── docs.yml
│   │   └── publish.yml
│   └── pull_request_template.md
├── docs/                    # Comprehensive documentation
│   ├── CONTRIBUTING.md      # Contribution guidelines
│   ├── DEVELOPER-NOTES.md   # Internal developer guide
│   ├── guides/              # Usage guides
│   ├── plugins/             # Plugin documentation
│   └── reference/           # API reference
├── examples/                # Example configurations
├── src/automax/             # Core package
│   ├── cli/                 # Command Line Interface
│   ├── core/                # Core logic and managers
│   │   ├── managers/        # Config, plugin, step managers
│   │   └── utils/           # Common utilities
│   └── plugins/             # Extensible plugin system (15+ plugins)
├── tests/                   # Test suite
│   ├── test_cli/            # CLI tests
│   ├── test_core/           # Core component tests
│   ├── test_plugins/        # Plugin tests
│   └── test_steps/          # Step execution tests
├── utils/                   # Developer utilities
├── pyproject.toml           # Build configuration
├── requirements.txt         # Dependencies
├── setup.py                 # Installation script
└── README.md                # Project overview
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

## 📚 Examples

Automax comes with comprehensive examples to help you get started:

### Basic Examples (`examples/basic/`)
- **Local Commands**: Execute system commands and check system info
- **File Operations**: Read, write, and manage files
- **HTTP Requests**: Make API calls and web requests
- **Network Checks**: Test connectivity and ports

### Advanced Examples (`examples/advanced/`)
- **Multi-Cloud Secrets**: Manage secrets across AWS, Azure, GCP, and HashiCorp Vault
- **CI/CD Pipeline**: Complete testing and deployment workflow
- **Data Processing**: ETL workflows with database integration
- **Monitoring Alerts**: System health checks with conditional notifications

### Running Examples
```bash
# List available examples
find examples/ -name "*.yaml" | sort

# Run a basic example
automax run --config examples/config/config.yaml --steps basic/local-commands

# Run an advanced example
automax run --config examples/config/config.yaml --steps advanced/ci-cd-pipeline
```

See the [Using Examples Guide](docs/guides/using-examples.md) for detailed instructions.

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
- **validate_plugin.py**: Validate all plugins in the plugins directory.
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

## 👥 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding new features, or improving documentation, your help is appreciated.

### Getting Started
- Read our [Contributing Guidelines](docs/CONTRIBUTING.md)
- Check the [Developer Notes](docs/DEVELOPER-NOTES.md) for internal conventions
- Explore the [plugin creation guide](docs/guides/creating-plugins.md)

### Quick Contribution
1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Make your changes and test: `pytest`
4. Ensure code quality: `isort . && black . && flake8 && docformatter -r .`
5. Commit your changes: `git commit -m "feat: add amazing feature"`
6. Push and open a Pull Request

### Development Tools
We use modern Python tooling:
- **Code formatting**: `isort . && black .`
- **Linting**: `flake8`
- **Docstring formatting**: `docformatter -r .`
- **Testing**: `pytest` with 90%+ coverage goal

See the [development utilities guide](docs/guides/development-utils.md) for more details.

---

## 💝 Donations

If you find Automax useful and would like to support its development, consider making a donation. Your contribution helps maintain the project and develop new features.

**Bitcoin Address:**
`36jDV57roGb4o59TwK1CB7viPrXToQHGiP`

---

## 🧾 License

This project is distributed under a Modified MIT License (Non-Commercial Use).

You are free to use, copy, modify, and distribute the software for non-commercial purposes under the terms of the MIT License.

Commercial use — including integration into products, services, or projects that generate revenue — requires a separate commercial license.
