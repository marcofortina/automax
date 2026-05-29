<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Security and access-control plugins

## SELinux

Use `security.selinux.mode`, `security.selinux.boolean`, `security.selinux.context`, `security.selinux.fcontext`,
`security.selinux.restorecon` and `security.selinux.port` for SELinux policy/runtime operations.
Keep context definitions and `restorecon` execution as separate substeps when a
reviewer must distinguish policy declaration from filesystem relabeling.

## AppArmor

Use `security.apparmor.status` for read-only status, `security.apparmor.profile` to load, enforce,
complain or remove one profile, and `security.apparmor.reload` to reload the AppArmor
service.


## PAM hardening

Use `security.pam.access`, `security.pam.faillock`, `security.pam.pwhistory`, `security.pam.succeed_if`,
`security.pam.service_line`, `security.pam.validate`, `security.pam.stack.facts` and `security.authselect.check` for
service-scoped PAM hardening and readback. PAM is authentication-critical: these
plugins avoid broad `/etc/pam.d/*` rewrites and operate only on explicit service
files or explicit service names. Mutating plugins back up files by default and
render the exact PAM line or policy file content in operator previews.

Recommended workflow:

```yaml
- id: inspect_pam
  use: security.pam.stack.facts
  with:
    service: sshd

- id: validate_pam
  use: security.pam.validate
  with:
    service: sshd

- id: enable_access
  use: security.pam.access
  with:
    entries:
      - "+ : deploy : 10.0.0.0/8"
    service: sshd
    backup: true
    sudo: true
```

`security.authselect.check` is read-only and validates the active RHEL-like authselect
profile/features. Use `security.authselect.profile` when the job intentionally changes the
authselect profile.

## SSH and sudo

`security.ssh.keygen` generates a remote SSH keypair with overwrite protection.
`security.ssh.config`, `security.ssh.known_hosts` and `security.ssh.authorized_key.add` cover SSH configuration,
known-host pinning and authorized key installation.

Use `security.sudo.dropin` for raw sudoers drop-ins, `security.sudo.rule` for structured sudoers
rules, and `security.sudo.validate` before relying on a sudoers change.

## SSH operational checks

Use `security.ssh.fingerprint`, `security.ssh.public_key`, `security.ssh.host_keygen`,
`security.ssh.authorized_key.check`, `security.ssh.authorized_key.remove` and `security.sshd.validate` to make SSH key and daemon
operations auditable before and after access-control changes.

## Certificate assertions

Use `security.pki.cert.fingerprint`, `security.pki.cert.key_match_check`, `security.pki.cert.san_check`,
`security.pki.cert.subject_check`, `security.pki.cert.issuer_check` and `security.pki.trust.install_bundle` for
certificate prechecks, trust-bundle installation and post-install validation.

## SSH key generation safeguards

`security.ssh.keygen` keeps no-overwrite behavior by default unless `force: true` is set.
It supports passphrase material via `passphrase_secret`, secret-safe manual
preview, public-key-only readback and fingerprint output after generation.

## Security operation completeness

AppArmor completeness plugins manage and validate profile modes explicitly:
`security.apparmor.enforce`, `security.apparmor.complain`, `security.apparmor.disable`,
`security.apparmor.profile_check` and `security.apparmor.validate`.

Auditd readback and rule-builder plugins provide active/persistent rule facts,
file watches, syscall rules, event search and backlog/lost-event assertions:
`security.audit.rules.facts`, `security.audit.watch`, `security.audit.syscall`, `security.audit.search` and
`security.audit.backlog_check`.

Sudo readback plugins verify effective privileges without changing sudoers:
`security.sudo.list`, `security.sudo.check` and `security.sudo.can_run`.

PAM stack assertion and backup plugins complement the mutating PAM plugins:
`security.pam.include_check`, `security.pam.module_check`, `security.pam.order_check`, `security.pam.backup` and
`security.pam.restore`. `security.pam.restore` requires `confirm: true` because it can affect login
paths.

## Capability preflight and redaction policy

Use `capabilities requirements` to derive remote tool requirements from the selected job plan after detecting each target OS family. Normal `automax run` performs the same OS-aware capability preflight implicitly before executing remote tools. When selected substeps use `sudo`, pass `automax run --sudo-password-env ENV_NAME` so the target account can keep password-protected sudo instead of a NOPASSWD sudoers drop-in. Use `capabilities install --sudo-password-env ENV_NAME` to install only missing dependency packages for the selected job and target OS; successful package-manager stdout/stderr is suppressed by default and can be shown with `--verbose` for troubleshooting.

The explicit capability plugins are:

```text
os.tool.check
os.tool.version_check
os.capability.check
automax.plugin.requirements
```

Use `security.secret.redact_check`, `security.secret.scan_output` and `security.secret.scan_preview` to validate that previews, command output and registered payloads do not expose declared secret values or common secret-shaped assignments such as `password=...`, bearer tokens or private-key blocks.
