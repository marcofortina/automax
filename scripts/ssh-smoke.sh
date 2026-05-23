#!/usr/bin/env bash
# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

set -euo pipefail

if [[ -z "${AUTOMAX_SSH_HOST:-}" || -z "${AUTOMAX_SSH_USER:-}" ]]; then
  echo "SKIP: set AUTOMAX_SSH_HOST and AUTOMAX_SSH_USER to run the real SSH smoke" >&2
  exit 77
fi

STATE_DIR="${AUTOMAX_STATE_DIR:-/tmp/automax-ssh-smoke-runs}"
WORK_DIR="${AUTOMAX_SMOKE_WORKDIR:-/tmp/automax-ssh-smoke}"
PORT="${AUTOMAX_SSH_PORT:-22}"
POLICY="${AUTOMAX_SSH_HOST_KEY_POLICY:-reject}"
if [[ "${POLICY}" != "reject" ]]; then
  echo "ERROR: AUTOMAX_SSH_HOST_KEY_POLICY must be reject; pre-populate known_hosts instead" >&2
  exit 2
fi
KNOWN_HOSTS="${AUTOMAX_SSH_KNOWN_HOSTS:-}"
KEY_FILE="${AUTOMAX_SSH_KEY_FILE:-}"
PASSWORD="${AUTOMAX_SSH_PASSWORD:-}"
CONNECT_TIMEOUT="${AUTOMAX_SSH_CONNECT_TIMEOUT:-10}"
COMMAND_TIMEOUT="${AUTOMAX_SSH_COMMAND_TIMEOUT:-60}"
SMOKE_PACKAGE="${AUTOMAX_SSH_SMOKE_PACKAGE:-curl}"
SMOKE_SERVICE="${AUTOMAX_SSH_SMOKE_SYSTEMD_SERVICE:-}"
SMOKE_USER="${AUTOMAX_SSH_SMOKE_USER:-automax_smoke_user}"
SMOKE_GROUP="${AUTOMAX_SSH_SMOKE_GROUP:-automax_smoke_group}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

mkdir -p "${TMP_DIR}/payload/dir" "${TMP_DIR}/downloads"
printf 'uploaded by automax\n' >"${TMP_DIR}/payload/upload.txt"
printf 'nested payload\n' >"${TMP_DIR}/payload/dir/nested.txt"
printf 'sync payload\n' >"${TMP_DIR}/payload/sync.txt"

cat >"${TMP_DIR}/inventory.yaml" <<YAML
servers:
  smoke:
    host: ${AUTOMAX_SSH_HOST}
    groups: [ssh]
    ssh:
      user: ${AUTOMAX_SSH_USER}
      port: ${PORT}
      missing_host_key_policy: ${POLICY}
      connect_timeout: ${CONNECT_TIMEOUT}
      command_timeout: ${COMMAND_TIMEOUT}
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
timeouts:
  ssh_connect: ${CONNECT_TIMEOUT}
  command: ${COMMAND_TIMEOUT}
tasks:
  - id: ssh_core
    targets: smoke
    tags: [ssh, smoke, core]
    steps:
      - id: filesystem_archive_transfer
        substeps:
          - id: clean_start
            use: fs.remove
            with:
              path: ${WORK_DIR}
              recursive: true
              force: true
          - id: mkdir
            use: fs.mkdir
            with:
              path: ${WORK_DIR}
              mode: "0700"
          - id: cd
            use: fs.cd
            with:
              path: ${WORK_DIR}
          - id: write_marker
            use: fs.write
            with:
              path: result.txt
              content: "automax-ssh-ok\n"
              mode: "0600"
          - id: read_marker
            use: fs.read
            with:
              path: result.txt
            register:
              ssh_smoke_output: stdout.trim
            artifacts:
              stdout: core/read-marker.txt
          - id: assert_marker
            use: assert.command
            with:
              command: "cat result.txt"
              equals: automax-ssh-ok
          - id: exists_marker
            use: fs.exists
            with:
              path: result.txt
              type: file
            register:
              marker_exists: data.exists
          - id: stat_marker
            use: fs.stat
            with:
              path: result.txt
            artifacts:
              data: core/stat-marker.json
          - id: ensure_line
            use: fs.line
            with:
              path: result.txt
              line: "line=old"
              state: present
          - id: replace_line
            use: fs.replace
            with:
              path: result.txt
              pattern: "line=old"
              replacement: "line=new"
          - id: copy_marker
            use: fs.copy
            with:
              src: result.txt
              dest: copied.txt
              overwrite: true
          - id: move_marker
            use: fs.move
            with:
              src: copied.txt
              dest: moved.txt
              overwrite: true
          - id: symlink_create
            use: fs.symlink.create
            with:
              src: moved.txt
              dest: moved.link
              force: true
          - id: symlink_remove
            use: fs.symlink.remove
            with:
              path: moved.link
          - id: find_files
            use: fs.find
            with:
              path: .
              patterns: ["*.txt"]
              type: file
              max_depth: 1
            artifacts:
              stdout: core/find-files.txt
          - id: chmod_marker
            use: fs.chmod
            with:
              path: moved.txt
              mode: "0600"
          - id: upload_file
            use: transfer.upload
            with:
              src: ${TMP_DIR}/payload/upload.txt
              dest: ${WORK_DIR}/uploaded.txt
          - id: upload_dir
            use: transfer.upload
            with:
              src: ${TMP_DIR}/payload/dir
              dest: ${WORK_DIR}/uploaded-dir
              recursive: true
          - id: sync_dir
            use: transfer.sync
            with:
              src: ${TMP_DIR}/payload
              dest: ${WORK_DIR}/synced
          - id: download_file
            use: transfer.download
            with:
              src: ${WORK_DIR}/uploaded.txt
              dest: ${TMP_DIR}/downloads/uploaded.txt
          - id: tar_workspace
            use: archive.tar
            with:
              source: ${WORK_DIR}/uploaded-dir
              dest: ${WORK_DIR}/uploaded-dir.tar.gz
              compression: gzip
              creates: ${WORK_DIR}/uploaded-dir.tar.gz
          - id: untar_workspace
            use: archive.untar
            with:
              archive: ${WORK_DIR}/uploaded-dir.tar.gz
              dest: ${WORK_DIR}/untar
              compression: gzip
              creates: ${WORK_DIR}/untar/uploaded-dir/nested.txt
          - id: zip_workspace
            use: archive.zip
            with:
              source: ${WORK_DIR}/uploaded-dir
              dest: ${WORK_DIR}/uploaded-dir.zip
              recursive: true
              creates: ${WORK_DIR}/uploaded-dir.zip
          - id: unzip_workspace
            use: archive.unzip
            with:
              archive: ${WORK_DIR}/uploaded-dir.zip
              dest: ${WORK_DIR}/unzip
              creates: ${WORK_DIR}/unzip/uploaded-dir/nested.txt
          - id: wait_file
            use: wait.file
            with:
              path: ${WORK_DIR}/uploaded.txt
              state: present
              type: file
              timeout: 10
              interval: 1
          - id: wait_path
            use: wait.path
            with:
              path: ${WORK_DIR}/untar
              state: present
              type: directory
              timeout: 10
              interval: 1
          - id: wait_command
            use: wait.command
            with:
              command: "cat ${WORK_DIR}/result.txt"
              contains: line=new
              timeout: 10
              interval: 1
          - id: start_background_process
            use: remote.command
            with:
              command: "sh -c 'sleep 30 >/dev/null 2>&1 &'"
          - id: wait_process
            use: wait.process
            with:
              pattern: "sleep 30"
              state: present
              timeout: 10
              interval: 1
          - id: assert_file
            use: assert.file
            with:
              path: ${WORK_DIR}/uploaded.txt
              state: present
              type: file
          - id: assert_path
            use: assert.path
            with:
              path: ${WORK_DIR}/untar
              state: present
              type: directory
          - id: assert_disk
            use: assert.disk
            with:
              path: ${WORK_DIR}
              min_free_mb: 1
          - id: assert_tcp
            use: assert.tcp
            with:
              host: ${AUTOMAX_SSH_HOST}
              port: ${PORT}
              connect_timeout: ${CONNECT_TIMEOUT}
          - id: cleanup_process
            use: process.kill
            with:
              pattern: "sleep 30"
              ignore_missing: true
          - id: cleanup_workspace
            use: fs.remove
            with:
              path: ${WORK_DIR}
              recursive: true
              force: true
YAML

if [[ -n "${SMOKE_SERVICE}" ]]; then
  cat >>"${TMP_DIR}/job.yaml" <<YAML

  - id: systemd_smoke
    targets: smoke
    tags: [ssh, smoke, systemd]
    steps:
      - id: systemd
        substeps:
          - id: status
            use: systemctl.status
            with:
              service: ${SMOKE_SERVICE}
              sudo: true
          - id: is_active
            use: systemctl.is_active
            with:
              service: ${SMOKE_SERVICE}
              sudo: true
              fail_on_inactive: false
          - id: is_enabled
            use: systemctl.is_enabled
            with:
              service: ${SMOKE_SERVICE}
              sudo: true
              fail_on_disabled: false
          - id: daemon_reload
            use: systemctl.daemon_reload
            with:
              sudo: true
YAML
fi

if [[ "${AUTOMAX_SSH_SMOKE_PKG:-0}" == "1" ]]; then
  cat >>"${TMP_DIR}/job.yaml" <<YAML

  - id: package_smoke
    targets: smoke
    tags: [ssh, smoke, package]
    steps:
      - id: packages
        substeps:
          - id: update_cache
            use: pkg.update_cache
            with:
              manager: auto
              sudo: true
          - id: query_package
            use: pkg.query
            with:
              name: ${SMOKE_PACKAGE}
              manager: auto
              sudo: true
YAML
fi

if [[ "${AUTOMAX_SSH_SMOKE_PRIVILEGED:-0}" == "1" ]]; then
  cat >>"${TMP_DIR}/job.yaml" <<YAML

  - id: privileged_identity_smoke
    targets: smoke
    tags: [ssh, smoke, privileged]
    steps:
      - id: identity
        substeps:
          - id: create_group
            use: group.create
            with:
              name: ${SMOKE_GROUP}
              system: true
              sudo: true
          - id: create_user
            use: user.create
            with:
              name: ${SMOKE_USER}
              group: ${SMOKE_GROUP}
              system: true
              shell: /usr/sbin/nologin
              create_home: false
              sudo: true
          - id: modify_user
            use: user.modify
            with:
              name: ${SMOKE_USER}
              comment: Automax smoke user
              sudo: true
          - id: remove_user
            use: user.remove
            with:
              name: ${SMOKE_USER}
              remove_home: true
              sudo: true
          - id: remove_group
            use: group.remove
            with:
              name: ${SMOKE_GROUP}
              sudo: true
YAML
fi

PYTHONPATH="${PYTHONPATH:-src}" python -m automax validate \
  --job "${TMP_DIR}/job.yaml" \
  --inventory "${TMP_DIR}/inventory.yaml" \
  --tags ssh

PYTHONPATH="${PYTHONPATH:-src}" python -m automax run \
  --job "${TMP_DIR}/job.yaml" \
  --inventory "${TMP_DIR}/inventory.yaml" \
  --state-dir "${STATE_DIR}" \
  --tags ssh
