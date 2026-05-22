# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
SQLite state store used for checkpoints, audit and resume.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterator, Optional

from automax.core.models import NodeStatus


class StateStoreError(ValueError):
    """Raised when run state cannot be loaded."""


class StateStore:
    """One SQLite database per run."""

    def __init__(self, state_dir: str | Path, run_id: str):
        self.state_dir = Path(state_dir).expanduser().resolve()
        self.run_id = run_id
        self.run_dir = self.state_dir / run_id
        self.db_path = self.run_dir / "state.sqlite"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @classmethod
    def open_existing(cls, state_dir: str | Path, run_id: str) -> "StateStore":
        run_dir = Path(state_dir).expanduser().resolve() / run_id
        if not (run_dir / "state.sqlite").exists():
            raise StateStoreError(f"run state not found: {run_id}")
        return cls(state_dir, run_id)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    job_path TEXT NOT NULL,
                    inventory_path TEXT,
                    vars_path TEXT,
                    secrets_path TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS nodes (
                    run_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    target TEXT NOT NULL,
                    task_id TEXT,
                    step_id TEXT,
                    substep_id TEXT,
                    status TEXT NOT NULL,
                    changed INTEGER NOT NULL DEFAULT 0,
                    rc INTEGER NOT NULL DEFAULT 0,
                    message TEXT NOT NULL DEFAULT '',
                    output_json TEXT NOT NULL DEFAULT '{}',
                    started_at TEXT,
                    ended_at TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(run_id, node_id, target)
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    node_id TEXT,
                    target TEXT,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    target TEXT NOT NULL,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def create_run(
        self,
        *,
        job_path: str,
        inventory_path: str | None,
        vars_path: str | None,
        secrets_path: str | None,
        metadata: Dict[str, Any],
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runs (
                    run_id, job_path, inventory_path, vars_path, secrets_path,
                    status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.run_id,
                    job_path,
                    inventory_path,
                    vars_path,
                    secrets_path,
                    NodeStatus.RUNNING.value,
                    json.dumps(metadata, sort_keys=True),
                ),
            )

    def get_run(self) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (self.run_id,)
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["metadata"] = json.loads(data.pop("metadata_json") or "{}")
        return data

    def update_run_status(self, status: NodeStatus) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE runs
                   SET status = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE run_id = ?
                """,
                (status.value, self.run_id),
            )

    def record_event(
        self,
        event_type: str,
        *,
        node_id: str | None = None,
        target: str | None = None,
        payload: Dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO events(run_id, event_type, node_id, target, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self.run_id,
                    event_type,
                    node_id,
                    target,
                    json.dumps(payload or {}, sort_keys=True),
                ),
            )

    def start_node(
        self,
        *,
        node_id: str,
        target: str,
        task_id: str,
        step_id: str,
        substep_id: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO nodes(
                    run_id, node_id, target, task_id, step_id, substep_id,
                    status, started_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(run_id, node_id, target) DO UPDATE SET
                    status = excluded.status,
                    started_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    message = '',
                    rc = 0
                """,
                (
                    self.run_id,
                    node_id,
                    target,
                    task_id,
                    step_id,
                    substep_id,
                    NodeStatus.RUNNING.value,
                ),
            )

    def finish_node(
        self,
        *,
        node_id: str,
        target: str,
        status: NodeStatus,
        changed: bool = False,
        rc: int = 0,
        message: str = "",
        output: Dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE nodes
                   SET status = ?, changed = ?, rc = ?, message = ?,
                       output_json = ?, ended_at = CURRENT_TIMESTAMP,
                       updated_at = CURRENT_TIMESTAMP
                 WHERE run_id = ? AND node_id = ? AND target = ?
                """,
                (
                    status.value,
                    1 if changed else 0,
                    rc,
                    message,
                    json.dumps(output or {}, sort_keys=True),
                    self.run_id,
                    node_id,
                    target,
                ),
            )

    def mark_skipped(
        self,
        *,
        node_id: str,
        target: str,
        task_id: str,
        step_id: str,
        substep_id: str | None,
        message: str,
    ) -> None:
        self.start_node(
            node_id=node_id,
            target=target,
            task_id=task_id,
            step_id=step_id,
            substep_id=substep_id,
        )
        self.finish_node(
            node_id=node_id,
            target=target,
            status=NodeStatus.SKIPPED,
            message=message,
        )


    @property
    def artifacts_dir(self) -> Path:
        """Directory containing files captured for this run."""
        path = self.run_dir / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_artifact(
        self,
        *,
        node_id: str,
        target: str,
        name: str,
        kind: str,
        content: str,
    ) -> Dict[str, Any]:
        """Write one textual artifact and register it in the state database."""
        relative = self._safe_relative_artifact_path(name)
        node_dir = self.artifacts_dir / self._safe_path_part(target) / self._safe_path_part(node_id)
        path = node_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = content.encode("utf-8")
        path.write_bytes(encoded)
        digest = hashlib.sha256(encoded).hexdigest()
        artifact = {
            "node_id": node_id,
            "target": target,
            "name": str(relative),
            "kind": kind,
            "path": str(path),
            "size": len(encoded),
            "sha256": digest,
        }
        self.record_artifact(**artifact)
        return artifact

    def record_artifact(
        self,
        *,
        node_id: str,
        target: str,
        name: str,
        kind: str,
        path: str,
        size: int,
        sha256: str,
    ) -> None:
        """Record one already-written artifact."""
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO artifacts(run_id, node_id, target, name, kind, path, size, sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (self.run_id, node_id, target, name, kind, path, int(size), sha256),
            )

    def list_artifacts(self) -> list[Dict[str, Any]]:
        """List artifacts captured for this run."""
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                  FROM artifacts
                 WHERE run_id = ?
                 ORDER BY created_at ASC, target ASC, node_id ASC, name ASC
                """,
                (self.run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _safe_path_part(value: str) -> str:
        return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)

    @staticmethod
    def _safe_relative_artifact_path(name: str) -> Path:
        relative = Path(str(name))
        if relative.is_absolute() or ".." in relative.parts:
            raise StateStoreError(f"unsafe artifact name: {name}")
        if not str(relative).strip() or str(relative) == ".":
            raise StateStoreError("artifact name cannot be empty")
        return relative

    def first_failed_node_id(self) -> Optional[str]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT node_id
                  FROM nodes
                 WHERE run_id = ? AND status = ?
                 ORDER BY updated_at ASC, node_id ASC
                 LIMIT 1
                """,
                (self.run_id, NodeStatus.FAILED.value),
            ).fetchone()
        return str(row["node_id"]) if row else None


    def node_status_map(self) -> dict[tuple[str, str], str]:
        """Return current node statuses keyed by (node_id, target)."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT node_id, target, status FROM nodes WHERE run_id = ?",
                (self.run_id,),
            ).fetchall()
        return {(str(row["node_id"]), str(row["target"])): str(row["status"]) for row in rows}

    def node_keys_by_status(self, statuses: set[str]) -> set[tuple[str, str]]:
        """Return node keys whose status is in the supplied set."""
        if not statuses:
            return set()
        placeholders = ",".join("?" for _ in statuses)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT node_id, target
                  FROM nodes
                 WHERE run_id = ? AND status IN ({placeholders})
                """,
                (self.run_id, *sorted(statuses)),
            ).fetchall()
        return {(str(row["node_id"]), str(row["target"])) for row in rows}

    def list_runs(self) -> list[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY created_at DESC"
            ).fetchall()
        result = []
        for row in rows:
            data = dict(row)
            data["metadata"] = json.loads(data.pop("metadata_json") or "{}")
            result.append(data)
        return result

    @staticmethod
    def list_all_runs(state_dir: str | Path) -> list[Dict[str, Any]]:
        state_path = Path(state_dir).expanduser().resolve()
        runs = []
        if not state_path.exists():
            return runs
        for db_path in sorted(state_path.glob("*/state.sqlite")):
            run_id = db_path.parent.name
            store = StateStore(state_path, run_id)
            run = store.get_run()
            if run:
                runs.append(run)
        return sorted(runs, key=lambda item: item["created_at"], reverse=True)
