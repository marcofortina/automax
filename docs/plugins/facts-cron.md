<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Facts and cron plugins

## Facts

Use `facts.gather` for a combined host snapshot, or the narrower read-only
plugins `facts.os`, `facts.network`, `facts.packages` and `facts.services` when a
job only needs one area. These plugins are precheck-friendly and do not change the
target.

## Cron

Use `cron.entry` for one managed cron.d entry and `cron.file` for a complete
cron.d file. Prefer systemd timers when the service model is systemd-native, and
use cron only when the target platform or operational requirement needs it.
