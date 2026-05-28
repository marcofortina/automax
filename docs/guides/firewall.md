<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Firewall management

Automax provides backend-specific firewall plugins instead of hiding backend differences behind one generic rule model.

## firewalld

```yaml
- id: open_https
  use: network.firewall.firewalld.port
  with:
    port: 443
    protocol: tcp
    zone: public
    state: present
    permanent: true
    reload: true
    sudo: true
```

Use `network.firewall.firewalld.service`, `network.firewall.firewalld.rich_rule` and `network.firewall.firewalld.reload` for service-based and rich-rule workflows.

## UFW

```yaml
- id: allow_ssh_from_private_net
  use: network.firewall.ufw.rule
  with:
    rule: allow
    port: 22
    protocol: tcp
    from: 10.0.0.0/8
    sudo: true
```

`network.firewall.ufw.status`, `network.firewall.ufw.enable` and `network.firewall.ufw.disable` are also available.

## nftables

Use `network.firewall.nftables.validate` before applying larger policies and `network.firewall.nftables.apply` for validated application.

```yaml
- id: apply_nftables_policy
  use: network.firewall.nftables.apply
  with:
    src: ./firewall/prod.nft
    sudo: true
```
