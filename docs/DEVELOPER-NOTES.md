# Developer Notes – Automax

Internal guide for maintainers and regular contributors.

## Commit Convention (Conventional Commits – based on project history)

We use **lowercase** types + imperative mood. No scope unless needed `(core)`, no `!` for breaking changes yet.

### Primary types (used in 100% of commits so far)
- `feat:` New features, plugins, managers
  Es: `feat: add SendEmail plugin`
- `docs:` README, CHANGELOG, docs/ files
  Es: `docs: update README with build instructions`
- `infra:` GitHub Actions, CI/CD workflows
  Es: `infra: add publish workflow`
- `build:` Packaging, pyproject.toml, setup.py, requirements.txt
  Es: `build: add pyproject.toml for build configuration`
- `setup:` Config files, utils, examples, pytest.ini
  Es: `setup: add offline validation utility scripts`
- `structure:` Folder skeletons, empty packages
  Es: `structure: add core package skeleton`
- `style:` Black/ruff formatting
  Es: `style: reformat config_manager.py and logger_manager.py with Black`
- `test:` Test files only
  Es: `test: add unit tests for plugins`
- `fix:` Bug fixes (used in branch names: fixes/docs)
  Es: `fix: restore step execution features from legacy system`
- `refactor:` Code refactoring without changing behavior
  Es: `refactor: replace argparse with Click`
- `security:` Security improvements, vulnerability fixes, and security-related configuration changes
  Es: `security: remove SSH keys and update configuration`

### Alternative types (use only if nothing above fits)
- `config:` → specific config files (es. pytest.ini, but we prefer setup)
- `project:` → high-level organization
- `misc:` → fallback (avoid when possible)

### Type Boundaries
- `setup:` vs `config:` → Use `setup:` for project setup files, `config:` for runtime configs
- `structure:` vs `feat:` → Use `structure:` for empty skeletons, `feat:` for functional code
- `docs:` vs `setup:` → Use `docs:` for documentation, `setup:` for configuration examples

### Avoid These
- `feat: added new plugin` → `feat: add new plugin` (imperative)
- `Docs: update readme` → `docs: update README` (lowercase)
- `fix(config): resolve issue` → `fix: resolve config issue` (no scope)
- `feat!: breaking change` → `feat: implement new approach` (no ! for now)
- **Merge commits**: `Merge PR #21: feat: implement feature` → `Merge PR #21: Implement Feature Description` (Title Case for merge descriptions)

### PR and Merge Convention

#### PR Title Format
```text
type: description
```
Example: `feat: add advanced output mapping with transformations between substeps`

#### PR Description
Use the template from `.github/pull_request_template.md` when creating pull requests.

#### Merge Commit Format
```text
Merge PR #PR_NUMBER: Title Case Description

[Concise description of implementation, benefits, and testing status]
```
Example:
```text
Merge PR #21: Implement Jinja2 Templating System for Dynamic Configurations

Complete implementation of Jinja2 templating across Automax core components, enabling dynamic configuration rendering
and advanced output transformations. All tests passing, backward compatibility maintained, and ready for production use.
```

### Quick Start for Contributors
1. Fork & Clone
2. `pip install -e .`
3. `pytest` (verify setup)
4. Make changes
5. Run code quality tools: `isort . && black . && flake8 && docformatter -r .`
6. `pytest` (test)
7. Commit & PR

## Commit Types Overview
| Type       | Use Case                          | Example |
|------------|-----------------------------------|---------|
| `feat`     | New features/plugins              | `feat: add S3 plugin` |
| `docs`     | Documentation                     | `docs: update README` |
| `infra`    | CI/CD workflows                   | `infra: add GitHub Actions` |
| `build`    | Packaging                         | `build: add setup.py` |
| `setup`    | Config files & utils              | `setup: add validation scripts` |
| `test`     | Test files                        | `test: add plugin tests` |
| `security` | Security improvements             | `security: remove SSH keys` |

Keep it clean, keep it fast! 🚀
