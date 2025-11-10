# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
and follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] - 2025-11-10

### Added
- Initial project structure: `automax/`, `examples/`, `tests/`, `utils/`.
- Core managers:
  - `ConfigManager`
  - `LoggerManager`
  - `PluginManager`
  - `ValidationManager`
- Plugin system with initial plugins:
  - Local and SSH commands: `local_command`, `ssh_command`
  - File plugins: `compress_file`, `uncompress_file`, `read_file_content`, `write_file_content`
  - Utility plugins: `check_network_connection`, `send_email`, `run_http_request`
- Example steps: `step1` and `step2` (Python + YAML integration)
- Core utility modules: `common_utils.py`, `log_utils.py`
- Unit tests for core managers
- CLI and programmatic API entry points: `cli.py`, `main.py`, `__main__.py`
- Offline validation scripts:
  - `validate_step.py`
  - `validate_plugins.py`
  - `check_step_deps.py`
  - `check_config.py`
  - `dry_run_validate.py`
  - `lint_yaml.py`
- Project setup files: `setup.py`, `pyproject.toml`, `.gitignore`, `logs/` directory
- Example SSH keys for testing
- MIT License

### Fixed
- Initial bugfixes and refinements in core utilities and plugin execution