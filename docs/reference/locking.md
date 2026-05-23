<!--
Copyright (C) 2026 Marco Fortina
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Run locking

Automax can protect operational runs from accidental concurrency with file-based locks.

```bash
automax run \
  --job jobs/deploy.yaml \
  --inventory inventory/prod.yaml \
  --lock
```

By default `--lock` uses `--lock-scope both`, which acquires:

- one job-level lock: `job:<job-name>`;
- one target-level lock for each selected server: `target:<server-name>`.

Available scopes:

```bash
automax run ... --lock --lock-scope job
automax run ... --lock --lock-scope target
automax run ... --lock --lock-scope both
```

Use `--lock-timeout` to wait for a lock instead of failing immediately:

```bash
automax run ... --lock --lock-timeout 30
```

Locks live next to the state directory, under `.automax/locks` when the default `.automax/runs` state path is used. Locks are released at the end of the run, including failed runs.
