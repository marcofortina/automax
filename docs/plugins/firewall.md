<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Firewall plugins

Automax keeps firewall backends explicit. Do not use a generic wrapper when the
operator needs backend-specific syntax, persistence and rollback behavior.

## firewalld

Use `network.firewall.firewalld.port`, `network.firewall.firewalld.service`, `network.firewall.firewalld.rich_rule` and
`network.firewall.firewalld.reload` on systems managed by firewalld. These plugins render
`firewall-cmd` commands and keep `permanent` and `reload` explicit.

## UFW

Use `network.firewall.ufw.rule`, `network.firewall.ufw.status`, `network.firewall.ufw.enable` and `network.firewall.ufw.disable` on Ubuntu-style UFW
hosts. `network.firewall.ufw.status` is read-only; enable/disable operations remain explicit
because they affect the active firewall policy.

## nftables

Use `network.firewall.nftables.validate` to run a syntax check before applying a ruleset, then
`network.firewall.nftables.apply` to install it. Keep the source ruleset under version control so
manual preview and job review can compare the intended policy.

## iptables

Use `network.firewall.iptables.rule` for one explicit rule, `network.firewall.iptables.save` to persist the active
ruleset to a file, and `network.firewall.iptables.restore` to load a saved ruleset. These plugins
are intentionally separate from nftables/firewalld/UFW because compatibility
layers and persistence paths differ by distribution.

## Readback and export plugins

Use `network.firewall.firewalld.status`, `network.firewall.firewalld.list` and `network.firewall.firewalld.zone` for firewalld
precheck and postcheck readback. Use `network.firewall.nftables.list` and `network.firewall.nftables.export` to
inspect or archive the active nftables ruleset. Use `network.firewall.iptables.list`,
`network.firewall.iptables.policy` and `network.firewall.iptables.chain` to inspect legacy iptables state before
and after runtime rule changes.

## Lifecycle safeguards

`network.firewall.firewalld.*` operations expose explicit runtime/permanent selection,
`query_only` readback and `reload_mode`. `network.firewall.iptables.rule` supports ordered
insertion, comments, `-w` wait handling, pre-change backups and `save_after`.
`network.firewall.nftables.apply` supports check-only validation, pre-apply backup, persistent
ruleset installation and service reload.

## Backend-specific firewall extras

firewalld backend extras manage source bindings, ICMP blocks, masquerading and
forward-port rules through explicit plugins: `network.firewall.firewalld.source`,
`network.firewall.firewalld.icmp_block`, `network.firewall.firewalld.masquerade` and `network.firewall.firewalld.forward_port`.

nftables extras provide readback assertion and rollback: `network.firewall.nftables.ruleset_check`
and `network.firewall.nftables.rollback_file`. Rollback requires `confirm: true`.

iptables extras provide deletion, rule existence assertion and counter assertion:
`network.firewall.iptables.delete`, `network.firewall.iptables.rule_check` and `network.firewall.iptables.counter_check`.
Deletion requires `confirm: true`.

UFW extras provide `network.firewall.ufw.delete` and `network.firewall.ufw.reset`. Both require `confirm: true`
because they remove firewall state.
