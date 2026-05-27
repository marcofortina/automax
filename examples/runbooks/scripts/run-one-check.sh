#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 NN-plugin | runbooks/NN-plugin.check.yaml" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_SECRETS="$ROOT/lab-secrets.example.yaml"
if [[ -f "$ROOT/lab-secrets.local.yaml" ]]; then
  DEFAULT_SECRETS="$ROOT/lab-secrets.local.yaml"
fi

SUDO_PASSWORD_ENV="${AUTOMAX_SUDO_PASSWORD_ENV:-AUTOMAX_SUDO_PASSWORD}"
if [[ -z "${!SUDO_PASSWORD_ENV:-}" ]]; then
  echo "Set $SUDO_PASSWORD_ENV, or set AUTOMAX_SUDO_PASSWORD_ENV to the environment variable that contains the sudo password." >&2
  exit 2
fi
JOB="$1"

case "$JOB" in
  runbooks/*.yaml)
    JOB_PATH="$ROOT/$JOB"
    ;;
  *.yaml)
    JOB_PATH="$ROOT/runbooks/$JOB"
    ;;
  *)
    JOB_PATH="$ROOT/runbooks/$JOB.check.yaml"
    ;;
esac

if [[ ! -f "$JOB_PATH" ]]; then
  echo "Runbook not found: $JOB_PATH" >&2
  exit 2
fi

python -m automax.cli.cli run \
  --job "$JOB_PATH" \
  --inventory "${INV:-$ROOT/lab-inventory.example.yaml}" \
  --vars "${VARS:-$ROOT/lab-vars.example.yaml}" \
  --secrets "${SECRETS:-$DEFAULT_SECRETS}" \
  --sudo-password-env "$SUDO_PASSWORD_ENV" \
  --var "automax_controller_fixture_root=$ROOT/controller-fixtures" \
  --check
