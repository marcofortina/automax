<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Command secrets

Automax supports `env`, `file` and `command` secret providers.

Use `provider: command` when a local helper can print a secret to stdout, for
example a password-store wrapper, an internal credential helper or a local
hardware-token integration.

```yaml
secrets:
  deploy_token:
    provider: command
    command: ["pass", "show", "prod/automax/deploy-token"]
    timeout: 10
```

The command must:

- run on the controller host;
- exit with code `0`;
- print the secret value to stdout;
- avoid printing sensitive diagnostics to stderr.

By default, the stdout value is stripped:

```yaml
secrets:
  raw_value:
    provider: command
    command: ["./scripts/read-secret"]
    strip: false
```

## Safe command form

Prefer list form. It does not use a shell:

```yaml
command: ["pass", "show", "prod/automax/token"]
```

String form is split without a shell by default:

```yaml
command: "pass show prod/automax/token"
```

Use `shell: true` only for trusted local commands that require shell features:

```yaml
secrets:
  token:
    provider: command
    command: "pass show prod/automax/token | head -n1"
    shell: true
```

Do not combine `shell: true` with untrusted variables.

## Relative working directory

`cwd` is resolved relative to the secrets YAML file:

```yaml
secrets:
  token:
    provider: command
    command: ["./get-token.sh"]
    cwd: helpers
```

## Masking

Resolved secrets are masked before stdout, stderr, messages, structured result
data and artifacts are persisted to the run state. Command provider errors do
not include captured stdout or stderr to avoid leaking secret material.
