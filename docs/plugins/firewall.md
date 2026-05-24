<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Firewall plugins

Automax keeps firewall backends explicit. Do not use a generic wrapper when the
operator needs backend-specific syntax, persistence and rollback behavior.

## firewalld

Use `firewalld.port`, `firewalld.service`, `firewalld.rich_rule` and
`firewalld.reload` on systems managed by firewalld. These plugins render
`firewall-cmd` commands and keep `permanent` and `reload` explicit.

## UFW

Use `ufw.rule`, `ufw.status`, `ufw.enable` and `ufw.disable` on Ubuntu-style UFW
hosts. `ufw.status` is read-only; enable/disable operations remain explicit
because they affect the active firewall policy.

## nftables

Use `nftables.validate` to run a syntax check before applying a ruleset, then
`nftables.apply` to install it. Keep the source ruleset under version control so
manual preview and job review can compare the intended policy.

## iptables

Use `iptables.rule` for one explicit rule, `iptables.save` to persist the active
ruleset to a file, and `iptables.restore` to load a saved ruleset. These plugins
are intentionally separate from nftables/firewalld/UFW because compatibility
layers and persistence paths differ by distribution.

## Readback and export plugins

Use `firewalld.status`, `firewalld.list` and `firewalld.zone` for firewalld
precheck and postcheck readback. Use `nftables.list` and `nftables.export` to
inspect or archive the active nftables ruleset. Use `iptables.list`,
`iptables.policy` and `iptables.chain` to inspect legacy iptables state before
and after runtime rule changes.

## Lifecycle safeguards

`firewalld.*` operations expose explicit runtime/permanent selection,
`query_only` readback and `reload_mode`. `iptables.rule` supports ordered
insertion, comments, `-w` wait handling, pre-change backups and `save_after`.
`nftables.apply` supports check-only validation, pre-apply backup, persistent
ruleset installation and service reload.

## Backend-specific firewall extras

firewalld backend extras manage source bindings, ICMP blocks, masquerading and
forward-port rules through explicit plugins: `firewalld.source`,
`firewalld.icmp_block`, `firewalld.masquerade` and `firewalld.forward_port`.

nftables extras provide readback assertion and rollback: `nftables.ruleset_assert`
and `nftables.rollback_file`. Rollback requires `confirm: true`.

iptables extras provide deletion, rule existence assertion and counter assertion:
`iptables.delete`, `iptables.exists_assert` and `iptables.counter_assert`.
Deletion requires `confirm: true`.

UFW extras provide `ufw.delete` and `ufw.reset`. Both require `confirm: true`
because they remove firewall state.
