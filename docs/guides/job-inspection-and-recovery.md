<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Job inspection and recovery

Automax provides job-scoped inspection commands for operators who need to verify
what a job will touch before running it, diagnose a failed substep, reproduce the
failed action manually and then restart from the next safe checkpoint.

These commands resolve the same job, inventory, variables, secrets, target
filters and tag filters used by `automax run`. They are intentionally scoped to
one job so the output describes the operation under review, not unrelated files
or inventory entries.

## Inspect selected targets

Use `automax inventory show` before a production run to confirm the resolved
server set:

```bash
automax inventory show \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --vars vars/prod.yaml \
  --secrets secrets/prod.yaml \
  --limit web
```

The command prints only targets selected by the job after applying `--limit`,
`--exclude`, `--tags` and `--skip-tags`.

## Prepare SSH known_hosts entries

Use `automax ssh known-hosts scan` before the first SSH run when targets are not
yet present in the configured known_hosts file:

```bash
automax ssh known-hosts scan \
  --inventory inventory/prod.yaml \
  --limit web \
  --output ~/.ssh/automax_known_hosts
```

Verify the printed fingerprints out-of-band before relying on the written file.
Automax still uses strict host-key rejection during real SSH runs.

## Render final variable context

Use `automax vars render` to see the final target-specific variable context,
masked secret names and selected nodes before a run:

```bash
automax vars render \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --vars vars/prod.yaml \
  --secrets secrets/prod.yaml \
  --limit web01
```

Secrets are listed by name only and rendered as `***`. This keeps the command
safe for CI logs and issue attachments while still showing which secret keys are
available to templates.

## Check only secrets used by the selected job

Use `automax secrets check` to verify that required secret providers can be read
without exposing secret values:

```bash
automax secrets check \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --secrets secrets/prod.yaml \
  --limit web
```

By default the command checks only secrets referenced by the resolved job plan.
Use `--all` when you explicitly want to check every secret declared in the
secrets file.

## Preview check-mode behavior

Use `automax plan --check` when you want a dry-run style view of the selected
substeps and their plugin-level check support:

```bash
automax plan --check \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --vars vars/prod.yaml \
  --secrets secrets/prod.yaml
```

`automax run --check` prints the same check payload and does not create run
state. This is useful in CI gates that must verify the plan without touching the
state directory.

## Preview file diffs

Use `automax plan --diff` to list every selected substep. File-oriented
plugins that support deterministic previews include a unified diff; other
plugins are shown with a reason explaining why no deterministic diff is
available:

```bash
automax plan --diff \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --vars vars/prod.yaml \
  --secrets secrets/prod.yaml
```

Secret values rendered into previews are masked before output. Non-file or
state-dependent plugins are still listed so operators can see the full selected
job shape.

## Compress or decompress standalone files

`archive.tar` already supports `.tar.gz`, `.tar.bz2` and `.tar.xz` through
`compression: auto`. Use `archive.compress` / `archive.decompress` for standalone
`.gz`, `.bz2` and `.xz` files that are not tar containers.

## Preserve file content before regex replacements

`fs.replace` can create a pre-change backup before writing replacements:

```yaml
- id: update_config
  use: fs.replace
  with:
    path: /etc/myapp/app.conf
    pattern: "^port=.*$"
    replacement: "port=8080"
    backup: true
    sudo: true
```

The backup is created only when the replacement actually changes the file.
`automax plan --diff` cannot read the remote file during planning, so
`fs.replace` emits a deterministic replacement plan showing path, regex,
replacement, count and backup target instead of pretending to know the final
remote diff.

## Failed substep diagnostics

When a text run substep fails, Automax prints the rendered operator command plus
masked stdout and stderr immediately below the failed status line. This makes a
failed lab or production run actionable without first opening the SQLite state or
re-rendering the command manually.

Example:

```text
[FAILED] web01 task.deploy:step.install:substep.restart rc=1 remote command failed
  commands:
    $ sudo -n systemctl restart nginx
  stdout: <empty>
  stderr:
    Job for nginx.service failed because the control process exited with error code.
```

The same redaction policy used for persisted run state is applied to command,
stdout and stderr diagnostics before printing. Successful substeps keep the
compact one-line output; use `automax commands render` when every command needs
to be displayed before execution.

## Render manual recovery commands

When a job fails, render copy/pasteable commands for the same selected substeps:

```bash
automax commands render \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --vars vars/prod.yaml \
  --secrets secrets/prod.yaml \
  --limit web01 \
  --tags install
```

The output includes the target, host, checkpoint and plugin name before each
command. Every selected substep is listed. Plugins that cannot safely render a
manual command are reported with a reason instead of inventing shell snippets.

A typical recovery loop is:

1. Run `automax runs show <run-id> --failed` to identify the failed checkpoint.
2. Run `automax commands render` with matching `--limit` and `--tags` filters.
3. Execute the printed command manually on the affected host or controller.
4. Fix the root cause outside Automax.
5. Restart from the next appropriate checkpoint with `automax resume --from` or
   `automax run --from`.

## Machine-readable output

All inspection commands support JSON output for CI or operator tooling:

```bash
automax inventory show --job job.yaml --inventory inventory.yaml --format=json
automax secrets check --job job.yaml --inventory inventory.yaml --secrets secrets.yaml --format=json
automax vars render --job job.yaml --inventory inventory.yaml --format=json
automax commands render --job job.yaml --inventory inventory.yaml --format=json
```
