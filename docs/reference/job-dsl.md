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

Use `if` with `then` and optional `else` to branch inside a step. Branches contain
normal substeps and can use previous registered outputs:

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
