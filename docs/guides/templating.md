# Templating

Automax uses Jinja2 to render job, inventory, variable and secret references.

Typical values available to templates are:

```text
vars      external and job-level variables
secrets   resolved secret values
server    current target server
outputs   values registered by previous substeps
```

Example:

```yaml
- id: make_release_dir
  use: fs.mkdir
  with:
    path: "/opt/{{ vars.app_name }}/{{ vars.version }}"
    owner: "{{ server.vars.owner }}"
    mode: "0755"
```

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

Undefined variables should fail fast during validation or execution. Do not rely
on implicit empty strings for infrastructure automation.
