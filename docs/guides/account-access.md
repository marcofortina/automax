<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Account access management

Automax includes account access plugins for common Linux operator tasks:

- `user.exists`, `user.lock`, `user.unlock`, `user.set_password`
- `group.exists`
- `security.ssh.authorized_key.add`
- `security.sudo.dropin`

Use `password_hash` with `user.set_password` whenever possible. Plaintext passwords are supported for operational compatibility, but command secrets or file secrets are preferred.

```yaml
- id: set_deploy_password
  use: user.set_password
  with:
    name: deploy
    password_hash: "{{ secrets.deploy_password_hash }}"
    sudo: true
```

```yaml
- id: install_deploy_key
  use: security.ssh.authorized_key.add
  with:
    user: deploy
    key: "{{ vars.deploy_public_key }}"
    state: present
    sudo: true
```

```yaml
- id: allow_restart
  use: security.sudo.dropin
  with:
    name: deploy-myapp
    content: "deploy ALL=(root) /bin/systemctl restart myapp"
    validate: true
    sudo: true
```
