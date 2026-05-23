<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Security reference

## SSH host keys

Production inventories should reject unknown host keys:

```yaml
ssh:
  known_hosts: ~/.ssh/known_hosts
  missing_host_key_policy: reject
```

Lab-only auto-add behavior must be explicit:

```yaml
ssh:
  missing_host_key_policy: auto_add
  allow_insecure_host_key_policy: true
```

Do not use that pattern for production inventories.

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

Current secret providers are `env` and `file`.

```yaml
secrets:
  token:
    provider: env
    name: AUTOMAX_TOKEN
```

Resolved secret values are masked before stdout, stderr, messages, structured
result data and artifacts are persisted to the run state.

## Sudo

Many remote plugins accept `sudo: true`. Use it only on the substeps that require
privilege escalation. Keep non-privileged checks non-privileged.
