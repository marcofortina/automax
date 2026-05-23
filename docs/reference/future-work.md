<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Future work

This page tracks product ideas that are intentionally not part of the current
implementation contract. Items listed here are not discarded; they are held
until real operating experience proves the right shape.

## Additional secret providers

The current secret providers are `env`, `file` and `command`. Future providers may include:

```text
Vault
AWS Secrets Manager
Azure Key Vault
Google Secret Manager
pass
1Password
```

These should be core secret providers, not job-action plugins, so secrets remain
resolved before templating and execution.

## Additional schema and output formats

Automax currently exports JSON Schema and supports JSON output for plan/run/resume
operator summaries. Future work may add additional formats without changing the
command shape, for example:

```bash
automax schema export --format=yaml
automax run --format=yaml ...
```

## Policy engine

A future policy layer may validate jobs before execution against local operating
rules. Example use cases:

```text
require approval for pkg.upgrade
forbid recursive fs.remove on production
forbid shell execution for selected targets
require --lock on production deploy jobs
```

The policy engine should stay separate from the job DSL so teams can apply
different guardrails to the same job definition in lab and production.

## Risk or danger summary

`plan` or `explain` may eventually classify potentially dangerous operations:

```text
low: assert.*, wait.*, fs.exists
medium: systemctl.restart, fs.template, transfer.upload
high: pkg.upgrade, user.remove, fs.remove recursive=true
```

This would give operators a quick review surface before running jobs on real
targets.

## Approval gates

Automax may support explicit operator approval points in interactive sessions:

```yaml
- id: approve_restart
  use: operator.approval
  with:
    message: Restart production web services?
```

CI and unattended runs would need a non-interactive approval policy such as
`--approve` or a signed approval file.


## Event stream contract

Run state already records events. A future contract may formalize an append-only
JSONL stream for external integrations:

```text
.automax/runs/<run-id>/events.jsonl
```

This could support CI summaries, dashboards, notifications or external audit
pipelines without coupling those integrations to SQLite internals.

## Deploy macros

Automax already has the primitives for release-style workflows:

```text
transfer.upload
archive.untar
fs.symlink.create
fs.symlink.remove
systemctl.restart
http.assert
wait.http
```

A future `deploy.*` macro family may wrap these into higher-level release and
rollback operations once the exact operational pattern is proven on real jobs.

## Native cloud inventory providers

Dynamic inventory currently supports file, command and HTTP providers. Native
cloud inventory providers may be added later if the command/HTTP model is not
enough:

```text
inventory.aws_ec2
inventory.azure_vm
inventory.gcp_compute
inventory.kubernetes
```

These should be inventory providers, not job-action plugins.

## Container and orchestration plugins

Container and orchestration support is useful, but not part of the current core
SSH job-runner contract:

```text
container.run
container.exec
container.compose
k8s.apply
k8s.rollout_status
helm.upgrade
```

They should be added only if they keep Automax focused on resumable operational
workflows rather than turning it into a broad platform clone.

## File ACL plugins

POSIX ACL support is useful for shared application directories, service users and
operator access, but it is not part of the current core plugin set. Future plugins
may include:

```text
acl.get
acl.set
acl.remove
acl.default_set
acl.default_remove
```

The implementation should be explicit about `setfacl`/`getfacl` availability and
should avoid silently emulating ACL behavior with broader `chmod` permissions.
