# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""PostgreSQL database plugin."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import PluginValidationError
from automax.plugins.db.base import DatabaseQueryPlugin, rows_from_cursor_description


class DbPostgresQueryPlugin(DatabaseQueryPlugin):
    """Run transactional PostgreSQL statements using optional psycopg."""

    name = "database.postgres.query"
    description = "Run PostgreSQL queries or statements from the controller."

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        connection = params.get("connection", {}) or {}
        if not connection.get("dsn") and not connection.get("database"):
            raise PluginValidationError("database.postgres.query requires connection.dsn or connection.database")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        try:
            import psycopg
        except ImportError as exc:
            return PluginResult.failure(message="install optional dependency: automax[postgres]", stderr=str(exc))

        connection = params.get("connection", {}) or {}
        statements = self._statements(params)
        query_params = self._query_params(params)
        output = str(params.get("output", "rows"))
        fetch = str(params.get("fetch", "all"))
        kwargs = {}
        if connection.get("dsn"):
            connect_args = (connection["dsn"],)
        else:
            connect_args = ()
            for key in ("host", "port", "user", "password"):
                if connection.get(key) is not None:
                    kwargs[key] = connection[key]
            kwargs["dbname"] = connection.get("database")
        rowcount = 0
        rows: list[dict[str, Any]] = []
        try:
            with psycopg.connect(*connect_args, autocommit=False, **kwargs) as conn:
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
            return PluginResult.failure(message="database.postgres.query failed", stderr=str(exc))
