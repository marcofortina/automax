#!/usr/bin/env bash
set -euo pipefail

KEEP_GOING=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-going)
      KEEP_GOING=1
      shift
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: run-all-checks.sh [--keep-going]

Run every per-plugin check runbook.

Options:
  --keep-going   Continue after failed runbooks and return a summary at the end.
                 The default remains fail-fast.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

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

failed_runbooks=()
passed_count=0
failed_count=0

for job in "$ROOT"/runbooks/*.check.yaml; do
  rel="${job#"$ROOT"/}"
  echo "== $rel =="
  if python -m automax.cli.cli run \
    --job "$job" \
    --inventory "${INV:-$ROOT/lab-inventory.example.yaml}" \
    --vars "${VARS:-$ROOT/lab-vars.example.yaml}" \
    --secrets "${SECRETS:-$DEFAULT_SECRETS}" \
    --sudo-password-env "$SUDO_PASSWORD_ENV" \
    --var "automax_controller_fixture_root=$ROOT/controller-fixtures" \
    --check; then
    passed_count=$((passed_count + 1))
  else
    rc=$?
    failed_count=$((failed_count + 1))
    failed_runbooks+=("$rel rc=$rc")
    if [[ "$KEEP_GOING" -ne 1 ]]; then
      exit "$rc"
    fi
  fi
  echo
done

if [[ "$KEEP_GOING" -eq 1 ]]; then
  echo "== run-all summary =="
  echo "passed: $passed_count"
  echo "failed: $failed_count"
  if [[ "$failed_count" -gt 0 ]]; then
    echo "failed runbooks:"
    printf '  %s\n' "${failed_runbooks[@]}"
    exit 1
  fi
fi
