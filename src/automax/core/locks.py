# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""File-based run locks for job and target concurrency control."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Iterable


class LockError(RuntimeError):
    """Raised when a lock cannot be acquired."""


@dataclass
class AcquiredLock:
    """One lock held by the current process."""

    name: str
    path: Path


class LockManager:
    """Atomic file lock manager using O_EXCL lock files."""

    def __init__(self, lock_dir: str | Path):
        self.lock_dir = Path(lock_dir).expanduser().resolve()
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._held: list[AcquiredLock] = []

    @classmethod
    def for_state_dir(cls, state_dir: str | Path) -> "LockManager":
        return cls(Path(state_dir).expanduser().resolve().parent / "locks")

    def acquire_many(self, names: Iterable[str], *, timeout: float = 0) -> list[AcquiredLock]:
        """Acquire all lock names or release partial acquisition on failure."""
        deadline = time.monotonic() + max(0.0, float(timeout))
        acquired: list[AcquiredLock] = []
        try:
            for name in sorted(set(names)):
                acquired.append(self.acquire(name, deadline=deadline))
        except Exception:
            self.release_many(acquired)
            raise
        return acquired

    def acquire(self, name: str, *, deadline: float | None = None) -> AcquiredLock:
        """Acquire one lock, waiting until the optional deadline."""
        path = self._path_for_name(name)
        payload = json.dumps(
            {
                "name": name,
                "pid": os.getpid(),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            sort_keys=True,
        )
        while True:
            try:
                fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                if deadline is None or time.monotonic() >= deadline:
                    raise LockError(f"lock already held: {name} ({path})")
                time.sleep(0.25)
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload + "\n")
            lock = AcquiredLock(name=name, path=path)
            self._held.append(lock)
            return lock

    def release_many(self, locks: Iterable[AcquiredLock]) -> None:
        for lock in reversed(list(locks)):
            self.release(lock)

    def release(self, lock: AcquiredLock) -> None:
        try:
            lock.path.unlink()
        except FileNotFoundError:
            # Lock release is idempotent; the lock file may already be gone.
            self._forget(lock)
            return
        self._forget(lock)

    def _forget(self, lock: AcquiredLock) -> None:
        self._held = [item for item in self._held if item.path != lock.path]

    def release_all(self) -> None:
        self.release_many(list(self._held))

    def _path_for_name(self, name: str) -> Path:
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
        safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)[:80]
        return self.lock_dir / f"{safe_name}-{digest}.lock"
