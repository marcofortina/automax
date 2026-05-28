<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# First SSH job

This guide runs a minimal command on a real remote host.

## Inventory

Create `inventory.yaml`:

```yaml
servers:
  web01:
    host: web01.example.com
    port: 22
    groups: [web]
    ssh:
      user: "{{ secrets.ssh_user }}"
      key_file: "{{ secrets.ssh_key_file }}"
      known_hosts: ~/.ssh/known_hosts
      missing_host_key_policy: reject
      allow_agent: false
      look_for_keys: false
```

## Secrets

Create `secrets.yaml`:

```yaml
secrets:
  ssh_user:
    provider: env
    name: AUTOMAX_SSH_USER
  ssh_key_file:
    provider: file
    path: ~/.ssh/automax-key-path
```

The file provider above reads the key path from a file. Example:

```bash
printf '%s\n' "$HOME/.ssh/id_ed25519" > ~/.ssh/automax-key-path
chmod 600 ~/.ssh/id_ed25519
export AUTOMAX_SSH_USER=deploy
```

## Job

Create `job.yaml`:

```yaml
apiVersion: automax.io/v1
kind: Job
metadata:
  name: first-ssh-job
tasks:
  - id: inspect
    targets: group:web
    steps:
      - id: shell
        substeps:
          - id: hostname
            use: remote.command
            with:
              command: hostname
            register:
              remote_hostname: stdout.trim
          - id: os_release
            use: fs.file.read
            with:
              path: /etc/os-release
```

Run:

```bash
automax validate --job job.yaml --inventory inventory.yaml --secrets secrets.yaml
automax plan --job job.yaml --inventory inventory.yaml --secrets secrets.yaml
automax run --job job.yaml --inventory inventory.yaml --secrets secrets.yaml
```

If the job uses sudo-enabled remote plugins and the remote account requires a sudo password, export it on the controller and pass only the environment variable name:

```bash
export AUTOMAX_SUDO_PASSWORD='...'
automax run --job job.yaml --inventory inventory.yaml --secrets secrets.yaml --sudo-password-env AUTOMAX_SUDO_PASSWORD
```

If the run fails, inspect and resume:

```bash
automax runs show <run-id>
automax resume <run-id> --skip-successful
# If resumed substeps need sudo authentication:
automax resume <run-id> --skip-successful --sudo-password-env AUTOMAX_SUDO_PASSWORD
```
