<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Security and access-control plugins

## SELinux

Use `selinux.mode`, `selinux.boolean`, `selinux.context`, `selinux.fcontext`,
`selinux.restorecon` and `selinux.port` for SELinux policy/runtime operations.
Keep context definitions and `restorecon` execution as separate substeps when a
reviewer must distinguish policy declaration from filesystem relabeling.

## AppArmor

Use `apparmor.status` for read-only status, `apparmor.profile` to load, enforce,
complain or remove one profile, and `apparmor.reload` to reload the AppArmor
service.

## SSH and sudo

`ssh.keygen` generates a remote SSH keypair with overwrite protection.
`ssh.config`, `ssh.known_hosts` and `ssh.authorized_key` cover SSH configuration,
known-host pinning and authorized key installation.

Use `sudoers.dropin` for raw sudoers drop-ins, `sudo.rule` for structured sudoers
rules, and `sudo.validate` before relying on a sudoers change.

## SSH operational checks

Use `ssh.fingerprint`, `ssh.public_key`, `ssh.host_keygen`,
`ssh.authorized_key_absent` and `sshd.validate` to make SSH key and daemon
operations auditable before and after access-control changes.

## Certificate assertions

Use `cert.fingerprint`, `cert.matches_key`, `cert.san_assert`,
`cert.subject_assert`, `cert.issuer_assert` and `cert.install_ca_bundle` for
certificate prechecks, trust-bundle installation and post-install validation.

## SSH key generation safeguards

`ssh.keygen` keeps no-overwrite behavior by default unless `force: true` is set.
It supports passphrase material via `passphrase_secret`, secret-safe manual
preview, public-key-only readback and fingerprint output after generation.
