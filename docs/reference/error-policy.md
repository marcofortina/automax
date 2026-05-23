<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Error policy

`errorPolicy` normalizes command results before retry and failure policy are
applied. It is intended for operational tools that return non-zero exit codes
while reporting diagnostics that an operator already decided are acceptable.

Typical examples include Oracle RAC prechecks, cluster validators, storage
checks, package probes and vendor installers that mix expected warnings with
real failures.

## Execution order

Automax evaluates result handling in this order:

```text
plugin result
  -> errorPolicy
  -> retry
  -> failurePolicy
```

`errorPolicy` decides whether a failed plugin result can become a warning or a
success. `failurePolicy` is only applied if the result remains failed.

## Basic example

```yaml
- id: oracle_cluvfy
  use: remote.command
  with:
    command: "runcluvfy.sh stage -pre crsinst -n rac1,rac2 -verbose"
  errorPolicy:
    acceptedRc: [1, 2, 3]
    expected:
      - stream: combined
        pattern: "PRVF-5436.*NTP"
        reason: "NTP validation is expected because chrony is managed externally"
      - stream: combined
        pattern: "PRVG-13602.*DNS"
        reason: "DNS warning accepted in this lab"
    fail:
      - stream: combined
        pattern: "ORA-[0-9]+"
      - stream: combined
        pattern: "CRS-[0-9]+"
    unmatched: fail
    acceptedStatus: warning
```

Semantics:

```text
rc=0       -> normal success
rc=1/2/3   -> stdout/stderr are normalized by errorPolicy
rc=4       -> immediate failure, because it is not in acceptedRc
```

`acceptedRc` is always a list. This allows operators to accept `1`, `2` and `3`
while still treating `4` as a hard failure.

## Fields

| Field | Default | Description |
|---|---:|---|
| `acceptedRc` | `[]` | List of non-zero return codes that may be normalized after stdout/stderr analysis. |
| `expected` | `[]` | Regex rules for diagnostics that are expected and can be removed from the failure analysis. |
| `fail` | `[]` | Regex rules that always keep the result failed when they match. |
| `unmatched` | `fail` | What to do with remaining non-empty stdout/stderr lines after expected lines are removed: `fail`, `warn` or `ignore`. |
| `acceptedStatus` | `warning` | Final status for an accepted failure: `warning` or `success`. |

## Rule format

Rules can be strings or mappings.

String shorthand:

```yaml
errorPolicy:
  acceptedRc: [1]
  expected:
    - "PRVF-5436.*NTP"
```

Mapping form:

```yaml
errorPolicy:
  acceptedRc: [1]
  expected:
    - stream: stderr
      pattern: "WARN-[0-9]+"
      reason: "Vendor warning accepted by runbook"
```

Supported streams:

```text
stdout
stderr
combined
message
```

`combined` means stdout plus stderr. The plugin message can still be matched
explicitly with `stream: message`, but it is not considered unmatched output by
default. This avoids generic messages like `remote command failed` blocking a
result whose real stdout/stderr diagnostics were accepted.

## Unmatched handling

`unmatched: fail` is the safest default:

```yaml
errorPolicy:
  acceptedRc: [1]
  expected:
    - "EXPECTED-WARNING"
  unmatched: fail
```

If any non-empty stdout/stderr line remains after expected diagnostics are
removed, the result stays failed.

`unmatched: warn` continues the job but keeps the node in warning state:

```yaml
errorPolicy:
  acceptedRc: [1]
  expected:
    - "EXPECTED-WARNING"
  unmatched: warn
```

`unmatched: ignore` should only be used when the command is known to print
non-diagnostic informational output that is safe to ignore.

## Warning status

An accepted failure with `acceptedStatus: warning` is stored as a warning node.
The job continues, the run exits with `0` when no hard failures remain, and run
summaries show warning counts separately:

```text
[WARN] rac1 task.oracle:step.precheck:substep.oracle_cluvfy rc=1 accepted failure by errorPolicy: 2 expected diagnostic(s), 0 unexpected diagnostic(s)

Automax run succeeded
Summary:
  success: 8
  warning: 1
  failed: 0
```

`automax runs show <run-id>` also lists warning nodes separately from failed
nodes.
