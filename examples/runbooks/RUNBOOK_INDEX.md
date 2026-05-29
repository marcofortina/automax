# Automax per-plugin smoke runbooks

Per-plugin runbooks only. No combined runbook, no reused runtime smoke flow, and no separate destructive workflow.

| File | Plugin/family | Substeps |
|---|---:|---:|
| `runbooks/02-apparmor.check.yaml` | `security.apparmor` | 8 |
| `runbooks/03-data-archive.check.yaml` | `data.archive/data.compression` | 20 |
| `runbooks/05-auditd.check.yaml` | `security.audit` | 8 |
| `runbooks/06-authselect.check.yaml` | `security.authselect` | 1 |
| `runbooks/07-data-backup-restore.check.yaml` | `data.backup/data.restore` | 10 |
| `runbooks/11-cert.check.yaml` | `security.pki.cert` | 11 |
| `runbooks/13-system-cron.check.yaml` | `system.cron.entry` | 5 |
| `runbooks/14-database.check.yaml` | `database` | 8 |
| `runbooks/15-data-download.check.yaml` | `data.download` | 1 |
| `runbooks/17-facts.check.yaml` | `os/network/system facts` | 5 |
| `runbooks/19-firewalld.check.yaml` | `network.firewall.firewalld` | 11 |
| `runbooks/20-fs.check.yaml` | `fs.acl` | 31 |
| `runbooks/22-group.check.yaml` | `identity.group` | 5 |
| `runbooks/26-network-http.check.yaml` | `network.http` | 3 |
| `runbooks/27-iptables.check.yaml` | `network.firewall.iptables` | 9 |
| `runbooks/28-system-journal.check.yaml` | `system.journal` | 2 |
| `runbooks/29-system-kernel.check.yaml` | `system.kernel.boot_param` | 8 |
| `runbooks/31-command-local.check.yaml` | `command.local` | 1 |
| `runbooks/32-system-log.check.yaml` | `system.log` | 2 |
| `runbooks/35-notify-mail.check.yaml` | `notify.mail` | 1 |
| `runbooks/38-network.check.yaml` | `network.link` | 14 |
| `runbooks/39-nftables.check.yaml` | `network.firewall.nftables` | 6 |
| `runbooks/40-pam.check.yaml` | `security.pam` | 14 |
| `runbooks/41-password.check.yaml` | `security.password` | 1 |
| `runbooks/43-pki.check.yaml` | `security.pki.trust` | 3 |
| `runbooks/45-automax-plugin.check.yaml` | `automax.plugin` | 1 |
| `runbooks/46-system-process.check.yaml` | `system.process` | 5 |
| `runbooks/47-command-remote.check.yaml` | `command.remote` | 1 |
| `runbooks/48-network-dns-facts.check.yaml` | `network.dns` | 2 |
| `runbooks/49-secret.check.yaml` | `security.secret` | 3 |
| `runbooks/50-selinux.check.yaml` | `security.selinux` | 6 |
| `runbooks/51-ssh.check.yaml` | `security.ssh.authorized_key` | 8 |
| `runbooks/52-sshd.check.yaml` | `security.sshd` | 2 |
| `runbooks/53-sudo.check.yaml` | `security.sudo` | 6 |
| `runbooks/56-system-kernel-sysctl.check.yaml` | `system.kernel.sysctl` | 7 |
| `runbooks/57-system.check.yaml` | `system` | 1 |
| `runbooks/58-system-service.check.yaml` | `system.systemd` | 12 |
| `runbooks/59-system-systemd.check.yaml` | `system.systemd` | 4 |
| `runbooks/62-data-transfer.check.yaml` | `data.transfer` | 4 |
| `runbooks/63-device-udev.check.yaml` | `device.udev` | 9 |
| `runbooks/64-ufw.check.yaml` | `network.firewall.ufw` | 6 |
| `runbooks/65-user.check.yaml` | `identity.user` | 11 |
