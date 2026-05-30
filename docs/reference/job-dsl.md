<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Job DSL reference

Automax jobs are external YAML files. They are not stored inside the Python
package and are passed explicitly with `--job`.

The supported schema is intentionally strict and versioned:

```yaml
apiVersion: automax.io/v1
kind: Job
metadata:
  name: deploy-app
vars:
  app_name: myapp
targets: group:web
strategy:
  mode: serial
failurePolicy:
  onFailure: stop_job
  onUnreachable: stop_host
tags: [deploy]
tasks:
  - id: install
    targets: group:web
    tags: [install]
    steps:
      - id: packages
        tags: [packages]
        substeps:
          - id: install_nginx
            use: os.package.install
            with:
              name: nginx
              sudo: true
```

## Hierarchy

The execution hierarchy has three explicit levels below the job:

```text
Job
  Task[]
    Step[]
      Substep[]
```

A task groups related work. A step opens one fresh SSH connection per target and
runs all of its substeps through that connection. A substep calls one plugin.

## Required fields

At job level:

```text
apiVersion: automax.io/v1
kind: Job
tasks: non-empty list
```

At task level:

```text
id
steps: non-empty list
```

At step level:

```text
id
substeps: non-empty list
```

At substep level:

```text
id
use
with: optional mapping
```

`plugin` and `params` are accepted by the engine for compatibility with early
internal drafts, but new job files should use only `use` and `with`.

## Targets

`targets` can be declared at job, task, step or substep level. More specific
scopes override broader scopes:

```yaml
targets: all
tasks:
  - id: web
    targets: group:web
    steps:
      - id: lb
        targets: group:loadbalancer
        substeps:
          - id: reload_lb
            targets: server:lb01
            use: system.service.reload
            with:
              service: haproxy.service
              sudo: true
```

Supported selectors:

```text
all
server:web01
web01
group:web
web
```

When substeps in the same step resolve to different target sets, Automax still
preserves the step-scoped SSH rule: it creates one execution group per target for
that step and runs only the matching substeps for that target.

## Strategy

Strategy can be declared at job, task or step level:

```yaml
strategy:
  mode: serial
```

```yaml
strategy:
  mode: parallel
  max_parallel: 5
```

```yaml
strategy:
  mode: rolling
  batch_size: 2
  pause_between_batches: 10
```

`parallel` and `rolling` group execution by step and substep while preserving the
step-scoped SSH connection model.

## Tags

Tags are inherited from job, task, step and substep. The effective tag set is used
by `--tags` and `--skip-tags`:

```bash
automax run --job job.yaml --inventory inventory.yaml --tags install --skip-tags dangerous
```

`--skip-tags` wins over `--tags` when a substep has both.

## Failure policy

Failure policy can be declared at job, task or step level:

```yaml
failurePolicy:
  onFailure: stop_job
  onUnreachable: stop_host
  maxFailedHosts: 1
```

Supported actions:

```text
stop_job
stop_task
stop_host
continue
```

`maxFailedHosts` stops the job after too many target hosts have failed.

## Error policy

`errorPolicy` can be declared at job, task, step or substep level. It runs before
retry and failure policy. Use it when a command returns a non-zero code but some
diagnostics are expected and should not block the workflow.

```yaml
errorPolicy:
  acceptedRc: [1, 2, 3]
  expected:
    - stream: combined
      pattern: "PRVF-5436.*NTP"
      reason: "Expected Oracle RAC precheck diagnostic"
  fail:
    - stream: combined
      pattern: "ORA-[0-9]+"
  unmatched: fail
  acceptedStatus: warning
```

A result that remains failed after `errorPolicy` is then handled by retry and
finally by `failurePolicy`. See [Error policy](error-policy.md).

## Conditions and flow control

A substep can include a `when` expression. The expression is rendered with Jinja2
and considered false only when it renders to `""`, `0`, `false`, `no` or `none`:

```yaml
- id: restart_only_when_enabled
  use: system.service.restart
  when: "{{ vars.restart_enabled }}"
  with:
    service: myapp.service
    sudo: true
```

Use scalar `if` with `then` and optional `else` to branch inside a step.
Branches contain normal substeps and can use previous registered outputs:

```yaml
- id: check_service
  use: system.service.active.check
  with:
    service: myapp.service
  register: service_state

- id: restart_or_start
  if: "{{ outputs.service_state.data.active }}"
  then:
    - id: restart
      use: system.service.restart
      with:
        service: myapp.service
        sudo: true
  else:
    - id: start
      use: system.service.start
      with:
        service: myapp.service
        sudo: true
```

For multi-branch logic, `if` can also be a list of ordered branches. Automax
executes the first branch whose `when` expression is true; `else` is optional and
must be the last branch when present:

```yaml
- id: grade_branch
  if:
    - when: "{{ x < 50 }}"
      then:
        - id: grade_f
          use: command.local.run
          with:
            command: "echo F"
    - when: "{{ x < 60 }}"
      then:
        - id: grade_d
          use: command.local.run
          with:
            command: "echo D"
    - when: "{{ x < 70 }}"
      then:
        - id: grade_c
          use: command.local.run
          with:
            command: "echo C"
    - when: "{{ x < 80 }}"
      then:
        - id: grade_b
          use: command.local.run
          with:
            command: "echo B"
    - else:
        - id: grade_a
          use: command.local.run
          with:
            command: "echo A"
```


Use `switch` / `case` / `default` when several branches compare the same value:

```yaml
- id: route_status
  switch: "{{ outputs.service.data.status }}"
  case:
    running:
      - id: ok
        echo: "service is running"
    failed:
      - id: restart
        use: system.service.restart
        with:
          service: myapp.service
          sudo: true
  default:
    - id: unknown
      fail: "Unknown service status: {{ outputs.service.data.status }}"
```


Use flow-level `retry` to repeat a nested block until all its substeps succeed or
attempts are exhausted:

```yaml
- id: retry_download
  retry:
    attempts: 3
    interval: 5s
    do:
      - id: fetch
        use: data.download.url
        with:
          url: "{{ artifact_url }}"
          dest: /tmp/app.tar.gz
```

Use `for` / `in` / `do` to repeat substeps for each value in a list. The loop
variable is available by its declared name, as `item`, and with loop metadata
under `loop` (`index`, `index0`, `first`, `last`, `length`):

```yaml
- id: list_members
  use: identity.group.member.list
  with:
    group: appusers
  register: members

- id: ensure_homes
  for: member
  in: "{{ outputs.members.data.members }}"
  do:
    - id: create_home
      use: fs.dir.create
      with:
        path: "/home/{{ member }}"
        owner: "{{ member }}"
        mode: "0750"
        sudo: true
```


Use `set` or `let` to store flow values without shell glue. Values are evaluated
as native Jinja expressions, then become available as `{{ name }}`, `vars.name`
and `outputs.name` for later substeps on the same target execution path:

```yaml
- id: compute_grade
  set:
    score: 65
    grade: C

- id: show_grade
  echo: "grade={{ grade }} score={{ vars.score }}"
```

Use `echo` for operator-visible messages without invoking a shell command:

```yaml
- id: show_member
  echo: "processing {{ item }}"
```




Use `noop` for explicit no-op branches, placeholders or documented skip paths:

```yaml
- id: nothing_to_do
  noop: "No action required on Debian targets"
```

Use `sleep` for an explicit pause without shelling out to `sleep`:

```yaml
- id: pause_after_restart
  sleep: 5s
```

Use `assert` to stop the current flow when a native Jinja condition is false:

```yaml
- id: require_service_ready
  assert: "{{ outputs.service_check.data.active }}"
  message: "Service is not active"
```

Use `fail` to stop the current flow explicitly with a rendered message:

```yaml
- id: reject_missing_service
  fail: "service {{ vars.service }} is missing"
  when: "{{ not outputs.service_check.data.exists }}"
```


Use `block` to group normal substeps under one condition, tag or logical id:

```yaml
- id: maintenance_changes
  when: "{{ vars.maintenance_window }}"
  block:
    - id: stop_service
      use: system.service.stop
      with:
        service: myapp.service
        sudo: true
    - id: update_package
      use: os.package.install
      with:
        name: myapp
        sudo: true
```

Use `try` / `rescue` / `always` to keep recovery and cleanup in YAML instead of
hiding it in a script:

```yaml
- id: guarded_change
  try:
    - id: apply
      use: fs.file.write
      with:
        path: /tmp/demo
        content: demo
  rescue:
    - id: rollback
      echo: "rollback would run here"
  always:
    - id: cleanup
      echo: "cleanup always runs"
```

Inside `for` loops, `break` stops the loop and `continue` skips the remaining
substeps for the current item. Use `when` to make them conditional:

```yaml
- id: loop_items
  for: item
  in: "{{ outputs.items.data.values }}"
  do:
    - id: skip_disabled
      continue: true
      when: "{{ item.disabled }}"
    - id: stop_at_marker
      break: true
      when: "{{ item.name == 'STOP' }}"
    - id: process
      echo: "{{ item.name }}"
```

Flow nodes execute on the same selected target as the parent substep. Nested
substeps can register outputs normally; repeated loop registrations overwrite the
same top-level name, while every execution is still stored under
`outputs.nodes.<node-id>`.

## Output registration

Plugins return a normalized result with `stdout`, `stderr`, `rc`, `changed`,
`skipped`, `message` and `data`. Substeps can register full results or selected
values:

```yaml
- id: read_version
  use: command.remote.run
  with:
    command: cat /opt/myapp/VERSION
  register:
    app_version: stdout.trim

- id: render_config
  use: fs.file.template
  with:
    src: ./templates/app.conf.j2
    dest: /etc/myapp/app.conf
```

Registered outputs are available as `outputs.*` in later substeps. Per-target
results are also stored under `outputs.targets.<target-name>`.
