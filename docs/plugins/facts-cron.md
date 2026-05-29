<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Facts and cron plugins

## Facts

Use `os.facts` for a combined host snapshot, or the narrower read-only
plugins `os.facts`, `network.link.facts`, `os.package.facts` and `system.service.facts` when a
job only needs one area. These plugins are precheck-friendly and do not change the
target.

## Cron

Use `system.cron.entry.add` for one managed cron.d entry and `system.cron.file` for a complete
cron.d file. Prefer systemd timers when the service model is systemd-native, and
use cron only when the target platform or operational requirement needs it.

## Cron readback and validation

Use `system.cron.entry.list` to inspect existing cron state, `system.cron.entry.remove` for explicit
removal of `/etc/cron.d` entries, and `system.cron.validate` to check cron file syntax
before installing or replacing a schedule file.
