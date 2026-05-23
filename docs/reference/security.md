<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Security reference

## Paramiko dependency floor

Automax requires `paramiko>=5.0.0,<6.0` so SSH transport uses the
post-4.x dependency line and avoids known older Paramiko RSA/SHA-1 handling
alerts. Keep the lower bound at or above 5.0.0 unless a future security review
explicitly changes it.

## SSH host keys

Production inventories should reject unknown host keys:

```yaml
ssh:
  known_hosts: ~/.ssh/known_hosts
  missing_host_key_policy: reject
```

Unknown host keys are rejected. For lab hosts, scan the host key to a dedicated
known-hosts file before running Automax:

```bash
automax ssh known-hosts scan --host lab01.example.com --output ~/.ssh/automax_known_hosts
```

The scanner prints SHA256 fingerprints for verification over a trusted channel.
For inventories, scan the selected targets without running a job:

```bash
automax ssh known-hosts scan \
  --inventory inventory/prod.yaml \
  --limit web \
  --output ~/.ssh/automax_known_hosts
```

```yaml
ssh:
  known_hosts: ~/.ssh/automax_known_hosts
  missing_host_key_policy: reject
```

## Private key permissions

Automax checks private key permissions by default. Use:

```bash
chmod 600 ~/.ssh/id_ed25519
```

rather than disabling the check.

## Agent and key discovery

For predictable automation, prefer explicit settings:

```yaml
ssh:
  allow_agent: false
  look_for_keys: false
  key_file: ~/.ssh/id_ed25519
```

## Secrets

Current secret providers are `env`, `file` and `command`.

```yaml
secrets:
  token:
    provider: env
    name: AUTOMAX_TOKEN

  deploy_token:
    provider: command
    command: ["pass", "show", "prod/automax/deploy-token"]
    timeout: 10
```

Resolved secret values are masked before stdout, stderr, messages, structured
result data and artifacts are persisted to the run state.

Command secrets run on the controller. Prefer list-form commands and keep
`shell: false` unless a trusted local helper explicitly needs shell features.
Command provider errors intentionally do not include captured stdout or stderr.

## Sudo

Many remote plugins accept `sudo: true`. Use it only on the substeps that require
privilege escalation. Keep non-privileged checks non-privileged.
