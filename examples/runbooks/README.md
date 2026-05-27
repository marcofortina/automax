# Automax per-plugin smoke runbooks

These examples live in the repository under `examples/runbooks`; no `/tmp` extraction step is required.

Contents:

- `runbooks/*.check.yaml`: one check-mode runbook per plugin or plugin family.
- `RUNBOOK_INDEX.md`: plugin index and substep counts.
- `lab-inventory.example.yaml`, `lab-vars.example.yaml`, `lab-secrets.example.yaml`: minimal lab examples.
- `controller-fixtures/`: local controller-side fixtures for plugins that need source files or directories.
- `scripts/`: small helpers to run one check or all checks.

These runbooks are intended for `automax run --check`. They validate rendering, parameter validation, preview/manual coverage, and per-plugin coverage one plugin at a time. They are not ordered runtime smoke flows and they are not destructive workflows.

## Setup

From the Automax repository:

```bash
cd examples/runbooks

export RB="$PWD"
export INV="$RB/lab-inventory.example.yaml"
export VARS="$RB/lab-vars.example.yaml"

cp lab-secrets.example.yaml lab-secrets.local.yaml
$EDITOR lab-secrets.local.yaml
export SECRETS="$RB/lab-secrets.local.yaml"

# Required by the helper scripts and by the explicit --sudo-password-env examples.
export AUTOMAX_SUDO_PASSWORD='...'
```

`lab-secrets.example.yaml` intentionally contains empty values only. Populate `lab-secrets.local.yaml` locally and do not commit it. The local file is ignored by the `examples/runbooks/.gitignore` rules.

`lab-vars.example.yaml` uses `controller-fixtures` as a relative path when commands are launched from `examples/runbooks`. The helper scripts pass an absolute path to avoid ambiguity.

## Run one plugin

Example for `ufw`:

```bash
python -m automax.cli.cli run \
  --job "$RB/runbooks/64-ufw.check.yaml" \
  --inventory "$INV" \
  --vars "$VARS" \
  --secrets "$SECRETS" \
  --sudo-password-env AUTOMAX_SUDO_PASSWORD \
  --var automax_controller_fixture_root="$RB/controller-fixtures" \
  --check
```

Or use the helper:

```bash
"$RB/scripts/run-one-check.sh" 64-ufw
```

The helper also accepts the full relative path:

```bash
"$RB/scripts/run-one-check.sh" runbooks/64-ufw.check.yaml
```

## Run all per-plugin check runbooks

```bash
"$RB/scripts/run-all-checks.sh"
```

The helpers always pass `--sudo-password-env` so password-protected sudo can be tested without installing NOPASSWD sudoers rules. They fail early if the selected sudo password environment variable is unset. Optional overrides:

```bash
export AUTOMAX_LAB_SUDO_PASSWORD='...'
INV=/path/to/inventory.yaml \
VARS=/path/to/vars.yaml \
SECRETS=/path/to/lab-secrets.local.yaml \
AUTOMAX_SUDO_PASSWORD_ENV=AUTOMAX_LAB_SUDO_PASSWORD \
"$RB/scripts/run-all-checks.sh"
```
