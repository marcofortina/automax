<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Firewall management

Automax provides backend-specific firewall plugins instead of hiding backend differences behind one generic rule model.

## firewalld

```yaml
- id: open_https
  use: firewalld.port
  with:
    port: 443
    protocol: tcp
    zone: public
    state: present
    permanent: true
    reload: true
    sudo: true
```

Use `firewalld.service`, `firewalld.rich_rule` and `firewalld.reload` for service-based and rich-rule workflows.

## UFW

```yaml
- id: allow_ssh_from_private_net
  use: ufw.rule
  with:
    rule: allow
    port: 22
    protocol: tcp
    from: 10.0.0.0/8
    sudo: true
```

`ufw.status`, `ufw.enable` and `ufw.disable` are also available.

## nftables

Use `nftables.validate` before applying larger policies and `nftables.apply` for validated application.

```yaml
- id: apply_nftables_policy
  use: nftables.apply
  with:
    src: ./firewall/prod.nft
    sudo: true
```
