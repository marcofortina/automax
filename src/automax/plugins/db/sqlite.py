# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SQLite database plugin."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import PluginValidationError
from automax.plugins.db.base import DatabaseQueryPlugin


class DbSqliteQueryPlugin(DatabaseQueryPlugin):
    """Run transactional SQLite statements from the controller."""

    name = "database.sqlite.query"
    description = "Run SQLite queries or statements from the controller."
    optional_params = DatabaseQueryPlugin.optional_params + ("path", "database")

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        connection = params.get("connection", {}) or {}
        database = params.get("path") or params.get("database") or connection.get("path") or connection.get("database")
        if not database:
            raise PluginValidationError("database.sqlite.query requires path/database or connection.path")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        connection = params.get("connection", {}) or {}
        database = params.get("path") or params.get("database") or connection.get("path") or connection.get("database")
        statements = self._statements(params)
        query_params = self._query_params(params)
        output = str(params.get("output", "rows"))
        fetch = str(params.get("fetch", "all"))
        Path(str(database)).expanduser().parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(Path(str(database)).expanduser()))
        conn.row_factory = sqlite3.Row
        rowcount = 0
        rows: list[dict[str, Any]] = []
        try:
            conn.execute("BEGIN")
            cursor = conn.cursor()
            for index, statement in enumerate(statements):
                params_for_statement = query_params if index == len(statements) - 1 else ()
                cursor.execute(statement, params_for_statement)
                if index == len(statements) - 1 and fetch != "none" and cursor.description:
                    raw_rows = cursor.fetchone() if fetch == "one" else cursor.fetchall()
                    if raw_rows is None:
                        rows = []
                    elif fetch == "one":
                        rows = [dict(raw_rows)]
                    else:
                        rows = [dict(row) for row in raw_rows]
                if cursor.rowcount and cursor.rowcount > 0:
                    rowcount += cursor.rowcount
            if bool(params.get("commit", True)):
                conn.commit()
            else:
                conn.rollback()
            return self._format_result(rows=rows, rowcount=rowcount, output=output, statements=statements)
        except Exception as exc:
            conn.rollback()
            return PluginResult.failure(message="database.sqlite.query failed", stderr=str(exc))
        finally:
            conn.close()
