#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${AUTOMAX_SSH_HOST:-}" || -z "${AUTOMAX_SSH_USER:-}" ]]; then
  echo "SKIP: set AUTOMAX_SSH_HOST and AUTOMAX_SSH_USER to run the real SSH smoke" >&2
  exit 77
fi

STATE_DIR="${AUTOMAX_STATE_DIR:-/tmp/automax-ssh-smoke-runs}"
WORK_DIR="${AUTOMAX_SMOKE_WORKDIR:-/tmp/automax-ssh-smoke}"
PORT="${AUTOMAX_SSH_PORT:-22}"
POLICY="${AUTOMAX_SSH_HOST_KEY_POLICY:-reject}"
KNOWN_HOSTS="${AUTOMAX_SSH_KNOWN_HOSTS:-}"
KEY_FILE="${AUTOMAX_SSH_KEY_FILE:-}"
PASSWORD="${AUTOMAX_SSH_PASSWORD:-}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

cat >"${TMP_DIR}/inventory.yaml" <<YAML
servers:
  smoke:
    host: ${AUTOMAX_SSH_HOST}
    ssh:
      user: ${AUTOMAX_SSH_USER}
      port: ${PORT}
      missing_host_key_policy: ${POLICY}
YAML

if [[ -n "${KNOWN_HOSTS}" ]]; then
  cat >>"${TMP_DIR}/inventory.yaml" <<YAML
      known_hosts: ${KNOWN_HOSTS}
YAML
fi
if [[ -n "${KEY_FILE}" ]]; then
  cat >>"${TMP_DIR}/inventory.yaml" <<YAML
      key_file: ${KEY_FILE}
YAML
fi
if [[ -n "${PASSWORD}" ]]; then
  cat >>"${TMP_DIR}/inventory.yaml" <<YAML
      password: ${PASSWORD}
YAML
fi

cat >"${TMP_DIR}/job.yaml" <<YAML
apiVersion: automax.io/v1
kind: Job
metadata:
  name: ssh-smoke
failurePolicy:
  onFailure: stop_job
strategy:
  mode: serial
tasks:
  - id: ssh_smoke
    targets: smoke
    tags: [ssh, smoke]
    steps:
      - id: workspace
        substeps:
          - id: mkdir
            use: fs.mkdir
            with:
              path: ${WORK_DIR}
              mode: "0700"
          - id: cd
            use: fs.cd
            with:
              path: ${WORK_DIR}
          - id: command
            use: remote.command
            with:
              command: "printf automax-ssh-ok > result.txt"
          - id: chmod
            use: fs.chmod
            with:
              path: result.txt
              mode: "0600"
          - id: verify
            use: remote.command
            with:
              command: "cat result.txt"
            register:
              ssh_smoke_output: stdout.trim
YAML

PYTHONPATH="${PYTHONPATH:-src}" python -m automax validate \
  --job "${TMP_DIR}/job.yaml" \
  --inventory "${TMP_DIR}/inventory.yaml" \
  --tags ssh

PYTHONPATH="${PYTHONPATH:-src}" python -m automax run \
  --job "${TMP_DIR}/job.yaml" \
  --inventory "${TMP_DIR}/inventory.yaml" \
  --state-dir "${STATE_DIR}" \
  --tags ssh
