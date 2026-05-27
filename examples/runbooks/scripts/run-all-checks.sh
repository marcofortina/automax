#!/usr/bin/env bash
set -euo pipefail

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

for job in "$ROOT"/runbooks/*.check.yaml; do
  rel="${job#"$ROOT"/}"
  echo "== $rel =="
  python -m automax.cli.cli run \
    --job "$job" \
    --inventory "${INV:-$ROOT/lab-inventory.example.yaml}" \
    --vars "${VARS:-$ROOT/lab-vars.example.yaml}" \
    --secrets "${SECRETS:-$DEFAULT_SECRETS}" \
    --sudo-password-env "$SUDO_PASSWORD_ENV" \
    --var "automax_controller_fixture_root=$ROOT/controller-fixtures" \
    --check
  echo
done
