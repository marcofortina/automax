# Automax TODO List

---

## Code Improvements (High/Medium Priority)

### High Priority
- [ ] **Migrate fully to modern build system**  
  Remove `setup.py` + `setup.cfg`. Use only `pyproject.toml` with Poetry or Hatch. Add `poetry.lock` for reproducible installs.
- [ ] **Add comprehensive type hints + static analysis**  
  Add type annotations to all functions/modules. Integrate `mypy --strict` and `ruff` (lint + format) in CI (`ci.yml`).
- [ ] **Switch to proper plugin discovery (entry points)**  
  Replace filesystem loading in `plugin_manager.py` with `setuptools entry_points` or `pluggy`. Allow external plugins via `pip install automax-plugin-xyz`.
- [ ] **Add environment variable overrides for config**  
  In `config_manager.py`, support `AUTOMAX__SECTION__KEY` syntax + Pydantic models for validation. Enable zero-config runs in CI/CD.
- [ ] **Improve security in examples**  
  Add clear README warning: "Demo SSH keys only – never commit real keys". Update `.gitignore` to exclude real `.ssh/` while keeping examples.

### Medium Priority
- [ ] **Upgrade logging to structured format**  
  Replace basic `logging` in `logger_manager.py` with `structlog` or JSON logging for better parsing in ELK/Splunk.
- [ ] **Enhance error handling & user messages**  
  In `exceptions.py` and throughout, show full traceback only in `--debug`. Always display clean, actionable console messages.
- [ ] **Add async support for plugins**  
  Make plugin execution async-ready (asyncio). Add optional `--parallel` flag with ThreadPoolExecutor fallback.
- [ ] **Expand test suite with integration tests**  
  Add tests using temporary directories + mocked SSH (e.g., `ssh2-python` mock or `paramiko` stub). Aim for >90% coverage.
- [ ] **Clean up repository artifacts**  
  Add `automax.egg-info/` and build artifacts to `.gitignore`.

---

## New Features Roadmap (Suggested Order)

### Short-term (1-2 weeks – High Impact)
- [ ] **Parallel step execution**  
  Build dependency graph in `step_manager.py` → run independent steps with `ThreadPoolExecutor` or `asyncio.gather`. Add `--parallel` flag.
- [ ] **Jinja2 templating in YAML**  
  Render `{{ variables }}` in step files using context/output from previous steps.
- [ ] **Secrets management**  
  Integrate `python-dotenv`, HashiCorp Vault, or AWS Secrets Manager for sensitive values (SSH keys, API tokens).

### Medium-term (2-4 weeks)
- [ ] **Graph visualization**  
  New command: `automax graph --format mermaid|graphviz` → output workflow diagram.
- [ ] **Conditionals & loops in YAML**  
  Add `when: "{{ prev.output.code == 0 }}"` and basic `for:` loops.
- [ ] **Extended output formats**  
  `automax run --output json|yaml > report.json` for CI integration.
- [ ] **More built-in plugins (pick 3-5)**  
  - Docker (build/run/push)  
  - Git (clone/commit/push)  
  - Slack/Teams notifications  
  - Database queries (psycopg/SQLAlchemy)  
  - AWS CLI wrapper  

### Long-term (4+ weeks – Bigger Scope)
- [ ] **Automatic notifications on failure**  
  Global post-step hook for Slack/Teams/Email (reuse `send_email` plugin).
- [ ] **Lightweight Web UI**  
  FastAPI or Streamlit dashboard: list steps, trigger runs, view logs/history.
- [ ] **Built-in scheduler**  
  `automax schedule "0 2 * * *" step1 step2` using APScheduler or cron.
- [ ] **Plugin template & docs**  
  Add `cookiecutter` template for new plugins + contribution guide.

---

## Quick Wins for Visibility (Do These First!)
- [ ] Add Shields.io badges to README (CI, PyPI, Coverage, License).
- [ ] Record & embed demo GIF (asciinema → `automax run step1 step2`).
- [ ] Publish v0.1.0 to PyPI (trigger `publish.yml` workflow).
- [ ] Create `CONTRIBUTING.md` + GitHub issue templates.

---

**Total items:** 10 high/medium improvements + 10 roadmap features.  
Prioritize **High** improvements first → then **Parallelism + Jinja2** → publish → community growth!

Let's crush this roadmap! 🚀  
Ping me when you complete something – I can review code or help implement the next item.