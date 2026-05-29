# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Oracle database plugin."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import PluginValidationError
from automax.plugins.db.base import DatabaseQueryPlugin, rows_from_cursor_description


class DbOracleQueryPlugin(DatabaseQueryPlugin):
    """Run transactional Oracle statements using optional python-oracledb."""

    name = "database.oracle.query"
    description = "Run Oracle queries or statements from the controller."

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        connection = params.get("connection", {}) or {}
        if not connection.get("dsn"):
            raise PluginValidationError("database.oracle.query requires connection.dsn")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        try:
            import oracledb
        except ImportError as exc:
            return PluginResult.failure(message="install optional dependency: automax[oracle]", stderr=str(exc))

        connection = params.get("connection", {}) or {}
        statements = self._statements(params)
        query_params = self._query_params(params)
        output = str(params.get("output", "rows"))
        fetch = str(params.get("fetch", "all"))
        rowcount = 0
        rows: list[dict[str, Any]] = []
        conn = None
        try:
            conn = oracledb.connect(
                user=connection.get("user"),
                password=connection.get("password"),
                dsn=connection.get("dsn"),
            )
            with conn.cursor() as cursor:
                for index, statement in enumerate(statements):
                    cursor.execute(statement, query_params if index == len(statements) - 1 else None)
                    if index == len(statements) - 1 and fetch != "none" and cursor.description:
                        raw_rows = cursor.fetchone() if fetch == "one" else cursor.fetchall()
                        raw_rows = [] if raw_rows is None else ([raw_rows] if fetch == "one" else raw_rows)
                        rows = rows_from_cursor_description(cursor.description, raw_rows)
                    if cursor.rowcount and cursor.rowcount > 0:
                        rowcount += cursor.rowcount
            if bool(params.get("commit", True)):
                conn.commit()
            else:
                conn.rollback()
            return self._format_result(rows=rows, rowcount=rowcount, output=output, statements=statements)
        except Exception as exc:
            if conn is not None:
                conn.rollback()
            return PluginResult.failure(message="database.oracle.query failed", stderr=str(exc))
        finally:
            if conn is not None:
                conn.close()
