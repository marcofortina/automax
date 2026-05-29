<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Extended SSH smoke

`scripts/ssh-smoke.sh` is the operator-facing runtime smoke for a real SSH host.
It is intentionally skipped in CI unless the target host is provided through
environment variables.

The smoke builds a temporary external inventory and job, then executes Automax
against the target host exactly like a real user workflow.

## Required environment

```bash
AUTOMAX_SSH_HOST=192.0.2.10
AUTOMAX_SSH_USER=deploy
```

Recommended secure defaults:

```bash
AUTOMAX_SSH_KEY_FILE=~/.ssh/id_ed25519
AUTOMAX_SSH_HOST_KEY_POLICY=reject
AUTOMAX_SSH_KNOWN_HOSTS=~/.ssh/known_hosts
```

Useful overrides:

```bash
AUTOMAX_SSH_PORT=22
AUTOMAX_STATE_DIR=/tmp/automax-ssh-smoke-runs
AUTOMAX_SMOKE_WORKDIR=/tmp/automax-ssh-smoke
AUTOMAX_SSH_CONNECT_TIMEOUT=10
AUTOMAX_SSH_COMMAND_TIMEOUT=60
```

## What the default smoke covers

The default smoke is non-destructive and should be safe for an unprivileged
remote user. It covers:

- `remote.command`
- `fs.dir.create`, `fs.dir.remove`, `fs.dir.exists`, `fs.dir.wait`
- `fs.file.exists`, `fs.file.wait`, `fs.cd`, `fs.file.write`, `fs.file.read`, `fs.object.stat`
- `fs.file.line`, `fs.file.replace`, `fs.object.copy`, `fs.object.move`, `fs.symlink.create`, `fs.symlink.remove`
- `fs.object.find`, `fs.permission.mode`
- `archive.tar`, `archive.untar`, `archive.zip`, `archive.unzip`
- `transfer.upload`, `transfer.download`, `transfer.sync`
- `system.process.wait`
- `storage.usage.disk_check`, `network.connectivity.port_check`
- artifact capture for stdout/stderr/data
- resume helpers through the normal run state store

Run it with:

```bash
./scripts/ssh-smoke.sh
```

The script exits with code `77` when `AUTOMAX_SSH_HOST` or `AUTOMAX_SSH_USER` is
missing, so it can be used by CI jobs as an optional runtime check.

## Optional privileged smoke

Some plugin families need sudo or can change host-level state. They are disabled
by default and must be enabled explicitly.

Package manager smoke:

```bash
AUTOMAX_SSH_SMOKE_PKG=1 \
AUTOMAX_SSH_SMOKE_PACKAGE=curl \
./scripts/ssh-smoke.sh
```

Systemd smoke against a harmless service chosen by the operator:

```bash
AUTOMAX_SSH_SMOKE_SYSTEMD_SERVICE=ssh \
./scripts/ssh-smoke.sh
```

User/group/process smoke:

```bash
AUTOMAX_SSH_SMOKE_PRIVILEGED=1 \
AUTOMAX_SSH_SMOKE_USER=automax_smoke_user \
AUTOMAX_SSH_SMOKE_GROUP=automax_smoke_group \
./scripts/ssh-smoke.sh
```

Only enable privileged smoke on disposable lab systems or hosts where creating
and deleting the selected user/group is acceptable.

## Expected output

A successful run prints the normal Automax operator summary and writes state to:

```text
${AUTOMAX_STATE_DIR:-/tmp/automax-ssh-smoke-runs}/<run-id>/state.sqlite
${AUTOMAX_STATE_DIR:-/tmp/automax-ssh-smoke-runs}/<run-id>/artifacts/
```

Useful follow-up commands:

```bash
automax runs list --state-dir /tmp/automax-ssh-smoke-runs
automax runs show <run-id> --state-dir /tmp/automax-ssh-smoke-runs
automax artifacts list <run-id> --state-dir /tmp/automax-ssh-smoke-runs
```
