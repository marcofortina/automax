# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
SQLite state store used for checkpoints, audit and resume.
"""

from __future__ import annotations

from contextlib import contextmanager
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
