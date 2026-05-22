# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""MySQL/MariaDB database plugin."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import PluginValidationError
from automax.plugins.db.base import DatabaseQueryPlugin


class DbMysqlQueryPlugin(DatabaseQueryPlugin):
    """Run transactional MySQL/MariaDB statements using optional PyMySQL."""

    name = "db.mysql.query"
    description = "Run MySQL/MariaDB queries or statements from the controller."

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        connection = params.get("connection", {}) or {}
        if not connection.get("database"):
            raise PluginValidationError("db.mysql.query requires connection.database")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as exc:
            return PluginResult.failure(message="install optional dependency: automax[mysql]", stderr=str(exc))

        connection = params.get("connection", {}) or {}
        statements = self._statements(params)
        query_params = self._query_params(params)
        output = str(params.get("output", "rows"))
        fetch = str(params.get("fetch", "all"))
        kwargs = {
            "host": connection.get("host", "localhost"),
            "port": int(connection.get("port", 3306)),
            "user": connection.get("user"),
            "password": connection.get("password"),
            "database": connection.get("database"),
            "cursorclass": DictCursor,
            "autocommit": False,
        }
        rowcount = 0
        rows: list[dict[str, Any]] = []
        conn = None
        try:
            conn = pymysql.connect(**kwargs)
            with conn.cursor() as cursor:
                for index, statement in enumerate(statements):
                    cursor.execute(statement, query_params if index == len(statements) - 1 else None)
                    if index == len(statements) - 1 and fetch != "none" and cursor.description:
                        raw_rows = cursor.fetchone() if fetch == "one" else cursor.fetchall()
                        rows = [] if raw_rows is None else ([raw_rows] if fetch == "one" else list(raw_rows))
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
            return PluginResult.failure(message="db.mysql.query failed", stderr=str(exc))
        finally:
            if conn is not None:
                conn.close()
