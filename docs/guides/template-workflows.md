# Template workflows

Automax supports configuration rendering through the `fs.template` plugin.
Templates are regular local Jinja2 files rendered by the controller and uploaded
to the remote target through the active step-scoped SSH connection.

The plugin is intended for configuration files, unit files and small text assets
that need deterministic rendering from inventory, variables, secrets and previous
outputs.

## Plugin

```yaml
- id: render_config
  use: fs.template
  with:
    src: ./templates/app.conf.j2
    dest: /etc/myapp/app.conf
    owner: root
    group: root
    mode: "0644"
    sudo: true
    values:
      app_name: myapp
      port: 8080
```

`src` is a path on the controller. `dest` is the destination path on the remote
target. The remote parent directory is created automatically.

## Template context

Templates can read these values:

```text
job          current job document
task         current task mapping
step         current step mapping
substep      current substep mapping
server       current target server
target       same object as server
vars         merged external/job/CLI/server variables
secrets      resolved env/file secrets
outputs      registered outputs from previous substeps
step_state   state shared by substeps within the same step
values       explicit per-template values from fs.template.with.values
```

Example template:

```jinja
# Managed by Automax
app_name={{ values.app_name }}
environment={{ vars.environment }}
server={{ server.name }}
port={{ values.port }}
```

## Idempotency

`fs.template` uploads rendered content to a remote temporary file and installs it
only when content differs from the destination. If the file already has the same
content, the plugin returns `changed=false`.

## Safety

Undefined template variables fail fast because Automax uses Jinja2
`StrictUndefined`. This is intentional: infrastructure automation should not
silently render broken configuration files.
