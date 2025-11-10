# Contributing to Automax

Thanks for your interest in Automax! 🚀  

This is a lightweight, YAML-based automation framework. All contributions are welcome: features, bug fixes, docs, tests, or ideas.

## How to Contribute

### Prerequisites
- Python 3.11+
- Git
- (Optional) Poetry for dependency management

### Initial Setup
1. **Fork** the repo → `https://github.com/marcofortina/automax/fork`
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/automax.git
   cd automax
   ```
3. **Set up environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .  # Install in development mode
   ```
4. **Create a branch** (use naming convention below):
   ```bash
   git checkout -b feature/my-awesome-feature  # or docs/update-readme, infra/add-workflow, etc.
   ```
5. **Code & Test**:
   - Follow Black style: `black .`
   - Add type hints everywhere
   - Write tests in `tests/` (pytest)
   - Validate changes with utilities below
   - Run test suite
6. **Commit** (see `DEVELOPER-NOTES.md` for conventions):
   ```bash
   git commit -m "feat: add parallel execution with asyncio"
   ```
7. **Push & PR**:
   ```bash
   git push origin your-branch
   ```
   - Open PR against `main`
   - Fill PR template (see below)
   - Request review (@marcofortina)

## Quick Contribution Flow
1. Fork & Clone
2. `pip install -e .`
3. `pytest` (verify setup)
4. Make changes
5. `black .` (format)
6. `pytest` (test)
7. Commit & PR

## Branch Naming
- `feat/` → new features/plugins
- `fix/` → bug fixes
- `docs/` → documentation
- `infra/` → CI/CD, workflows
- `build/` → packaging, pyproject.toml
- `setup/` → configs, utils, examples
- `structure/` → skeletons, refactoring
- `style/` → formatting, linting
- `test/` → tests only
- `release/` → version bumps, changelog

## Code Style
- Python 3.11+
- Black formatting (`black .`)
- Type hints + mypy strict
- Conventional Commits (see `DEVELOPER-NOTES.md`)

## Testing
Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=automax
```

Run specific test file:
```bash
pytest tests/test_plugins/test_ssh_command.py
```

Run tests in parallel:
```bash
pytest -n auto
```

Run with verbose output:
```bash
pytest -v
```

- 90%+ coverage goal
- Unit + integration tests
- Mock external services (SSH, HTTP, Email)

## Validation Utilities
Dry-run validation:
```bash
python utils/validate_step.py examples/steps/step1/step1.yaml
```

Check step dependencies:
```bash
python utils/check_step_deps.py examples/steps/
```

Lint YAML files:
```bash
python utils/lint_yaml.py examples/config/config.yaml
```

Validate plugins:
```bash
python utils/validate_plugins.py
```

Dry-run validate entire project:
```bash
python utils/dry_run_validate.py
```

## Pull Request Template
Description
[Brief description of changes]

Type of Change
- [ ] feat: New feature
- [ ] fix: Bug fix
- [ ] docs: Documentation
- [ ] test: Tests
- [ ] infra: CI/CD
- [ ] build: Packaging
- [ ] setup: Configuration

Checklist
- [ ] Code follows style guidelines (`black .`)
- [ ] Tests added/updated (`pytest`)
- [ ] Documentation updated
- [ ] Branch naming follows convention
- [ ] Commit messages follow conventional commits

Testing Performed
- [ ] Unit tests added
- [ ] Integration tests updated
- [ ] Manual testing completed

Screenshots/Logs (if applicable)
[Add relevant screenshots or log excerpts]

Related Issues
Fixes # [Issue number]

Notes
[Any additional information]

## Debugging
- Check logs in `logs/` directory
- Use `--verbose` flag when available
- Validate YAML syntax before running
- Test plugins individually before integration

## Releasing
- Maintainer only: tag `vX.Y.Z` → GitHub Actions publishes to PyPI
- Update `CHANGELOG.md`
- Verify all tests pass
- Check documentation is current

## Questions?
Open an issue or discussion on GitHub.

Happy automating! 🛠️
