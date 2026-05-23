<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Retry policy

Automax supports inherited retry policies on jobs, tasks, steps and substeps.
The closest scope wins, so a substep can override a job-level default.

Retry is intended for transient operational failures: temporary package-manager
locks, services that need another restart attempt, short-lived network glitches,
or remote commands that can safely be retried.

## Basic example

```yaml
retry:
  attempts: 3
  delay: 5
  backoff: fixed
```

```yaml
apiVersion: automax.io/v1
kind: Job
metadata:
  name: retry-demo
retry:
  attempts: 2
  delay: 1
tasks:
  - id: deploy
    targets: group:web
    steps:
      - id: restart
        substeps:
          - id: restart_service
            use: systemctl.restart
            retry:
              attempts: 3
              delay: 2
              backoff: exponential
              max_delay: 10
            with:
              service: myapp
              sudo: true
```

## Fields

| Field | Default | Description |
|---|---:|---|
| `attempts` | `1` | Total attempts, including the first execution. |
| `delay` | `0` | Delay in seconds before the next attempt. |
| `backoff` | `fixed` | `fixed` or `exponential`. |
| `max_delay` | unset | Maximum delay when exponential backoff is used. |
| `retry_on_rc` | unset | Optional list of return codes eligible for retry. Without it, every failed result can retry. |

Camel-case aliases `maxDelay` and `retryOnRc` are accepted for operators who
prefer that style, but new job files should use snake_case.

## Visual retry output

Text runs print retry attempts before the final result:

```text
[RETRY] web01 task.deploy:step.restart:substep.restart_service attempt=1/3 rc=1 next=2 delay=2s systemctl failed
[RETRY] web01 task.deploy:step.restart:substep.restart_service attempt=2/3 rc=1 next=3 delay=4s systemctl failed
[OK] web01 task.deploy:step.restart:substep.restart_service rc=0
```

The final node output also records attempt metadata in the run state:

```json
{
  "data": {
    "attempt": 3,
    "attempts": [
      {"attempt": 1, "ok": false, "rc": 1, "message": "systemctl failed"},
      {"attempt": 2, "ok": false, "rc": 1, "message": "systemctl failed"},
      {"attempt": 3, "ok": true, "rc": 0, "message": ""}
    ]
  }
}
```

## Retry and failure policy

Retry is evaluated before `failurePolicy`. A substep only reaches failure policy
after all retry attempts are exhausted or after a return code that is not listed
in `retry_on_rc`.
