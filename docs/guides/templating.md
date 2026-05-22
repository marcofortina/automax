<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Templating

Automax uses Jinja2 with `StrictUndefined` to render job structures and plugin
parameters. Undefined variables fail fast instead of silently becoming empty
strings.

## Context available during substep execution

```text
job          current job document
task         current task mapping
step         current step mapping
substep      current substep mapping
server       current target server
target       same object as server
vars         merged variables for this target
secrets      resolved env/file secret values
outputs      values registered by previous substeps
step_state   values shared by plugins in the same step
```

`fs.template` also exposes `values`, the explicit mapping passed through
`fs.template.with.values`.

## Variables

```yaml
- id: make_release_dir
  use: fs.mkdir
  with:
    path: "/opt/{{ vars.app_name }}/{{ vars.version }}"
    owner: "{{ server.vars.owner }}"
    mode: "0755"
```

## Registered outputs

Registered outputs can be reused later in the same run:

```yaml
- id: get_user
  use: remote.command
  with:
    command: whoami
  register:
    remote_user: stdout.trim

- id: create_dir
  use: fs.mkdir
  with:
    path: /opt/app
    owner: "{{ outputs.remote_user }}"
```

`register` can also store the full plugin result by using a string:

```yaml
- id: stat_app
  use: fs.stat
  with:
    path: /opt/app
  register: app_stat
```

The full result then becomes available as `outputs.app_stat`.
