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


## PAM hardening

Use `pam.access`, `pam.faillock`, `pam.pwhistory`, `pam.succeed_if`,
`pam.service_line`, `pam.validate`, `pam.stack_facts` and `pam.authselect` for
service-scoped PAM hardening and readback. PAM is authentication-critical: these
plugins avoid broad `/etc/pam.d/*` rewrites and operate only on explicit service
files or explicit service names. Mutating plugins back up files by default and
render the exact PAM line or policy file content in operator previews.

Recommended workflow:

```yaml
- id: inspect_pam
  use: pam.stack_facts
  with:
    service: sshd

- id: validate_pam
  use: pam.validate
  with:
    service: sshd

- id: enable_access
  use: pam.access
  with:
    entries:
      - "+ : deploy : 10.0.0.0/8"
    service: sshd
    backup: true
    sudo: true
```

`pam.authselect` is read-only and validates the active RHEL-like authselect
profile/features. Use `authselect.profile` when the job intentionally changes the
authselect profile.

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

## Security operation completeness

AppArmor completeness plugins manage and validate profile modes explicitly:
`apparmor.enforce`, `apparmor.complain`, `apparmor.disable`,
`apparmor.profile_assert` and `apparmor.parser_validate`.

Auditd readback and rule-builder plugins provide active/persistent rule facts,
file watches, syscall rules, event search and backlog/lost-event assertions:
`auditd.rules_facts`, `auditd.watch`, `auditd.syscall`, `auditd.search` and
`auditd.backlog_assert`.

Sudo readback plugins verify effective privileges without changing sudoers:
`sudo.list`, `sudo.assert` and `sudo.can_run`.

PAM stack assertion and backup plugins complement the mutating PAM plugins:
`pam.include_assert`, `pam.module_assert`, `pam.order_assert`, `pam.backup` and
`pam.restore`. `pam.restore` requires `confirm: true` because it can affect login
paths.

## Capability preflight and redaction policy

Use `capabilities requirements` to derive remote tool requirements from the selected job plan after detecting each target OS family. Normal `automax run` performs the same OS-aware capability preflight implicitly before executing remote tools. When selected substeps use `sudo`, pass `automax run --sudo-password-env ENV_NAME` so the target account can keep password-protected sudo instead of a NOPASSWD sudoers drop-in. Use `capabilities install --sudo-password-env ENV_NAME` to install only missing dependency packages for the selected job and target OS.

The explicit capability plugins are:

```text
tool.exists
tool.version_assert
capability.assert
plugin.requirements
```

Use `secret.redact_assert`, `secret.scan_output` and `secret.scan_preview` to validate that previews, command output and registered payloads do not expose declared secret values or common secret-shaped assignments such as `password=...`, bearer tokens or private-key blocks.
