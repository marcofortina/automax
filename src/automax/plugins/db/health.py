# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Database health-check plugin."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import quote


class DbHealthPlugin(BasePlugin):
    """Run read-only health checks against supported database engines."""

    name = "db.health"
    description = "Run read-only controller-side database health checks."
    required_params = ("engine",)
    optional_params = ("connection", "path", "checks", "timeout", "output")
    opens_remote_session = False
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        engine = str(params["engine"])
        if engine not in {"sqlite", "postgres", "mysql", "oracle"}:
            raise PluginValidationError("db.health engine must be sqlite, postgres, mysql or oracle")
        checks = self._checks(params)
        allowed = {
            "connect",
            "select",
            "version",
            "integrity",
            "read_only",
            "recovery",
        }
        unknown = sorted(set(checks) - allowed)
        if unknown:
            raise PluginValidationError(f"unsupported db.health checks: {', '.join(unknown)}")
        if engine == "sqlite" and not self._sqlite_path(params):
            raise PluginValidationError("db.health engine=sqlite requires path/database or connection.path")

    def _checks(self, params: Dict[str, Any]) -> list[str]:
        raw = params.get("checks") or ["connect", "select", "version"]
        if isinstance(raw, str):
            return [raw]
        return [str(item) for item in raw]

    def _sqlite_path(self, params: Dict[str, Any]) -> str | None:
        connection = params.get("connection", {}) or {}
        return params.get("path") or params.get("database") or connection.get("path") or connection.get("database")

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "db.health is a read-only controller-side database health check"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        engine = str(params["engine"])
        checks = self._checks(params)
        connection = params.get("connection", {}) or {}
        if engine == "sqlite":
            database = self._sqlite_path(params)
            commands = [f"sqlite3 -readonly {quote(database)} 'SELECT 1;'"]
            if "integrity" in checks:
                commands.append(f"sqlite3 -readonly {quote(database)} 'PRAGMA integrity_check;'")
            return commands
        if engine == "postgres":
            host = connection.get("host", "localhost")
            database = connection.get("database", connection.get("dbname", "postgres"))
            user = connection.get("user")
            user_part = f" -U {quote(user)}" if user else ""
            return [f"PGPASSWORD=*** psql -h {quote(host)}{user_part} -d {quote(database)} -c 'SELECT 1;'"]
        if engine == "mysql":
            host = connection.get("host", "localhost")
            database = connection.get("database")
            user = connection.get("user")
            parts = ["mysql", "--password=***", "-h", quote(host)]
            if user:
                parts.extend(["-u", quote(user)])
            if database:
                parts.append(quote(database))
            parts.extend(["-e", quote("SELECT 1;")])
            return [" ".join(parts)]
        return ["sqlplus -L '<user>/<password>@<dsn>' <<'SQL'\nSELECT 1 FROM dual;\nSQL"]

    def _format(self, data: Dict[str, Any], params: Dict[str, Any]) -> PluginResult:
        output = str(params.get("output", "json"))
        if output == "none":
            stdout = ""
        elif output == "summary":
            state = "ok" if data.get("healthy") else "not healthy"
            stdout = f"{data['engine']} health {state} in {data['latency_ms']} ms"
        else:
            stdout = json.dumps(data, default=str, sort_keys=True)
        return PluginResult.success(changed=False, stdout=stdout, data=data)

    def _health_predicate(self, data: Dict[str, Any]) -> bool:
        checks = data.get("checks", {})
        if checks and not all(bool(value) for value in checks.values()):
            return False
        if data.get("integrity") not in {None, "ok"}:
            return False
        return True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        engine = str(params["engine"])
        started = time.monotonic()
        try:
            if engine == "sqlite":
                data = self._sqlite_health(params)
            elif engine == "postgres":
                data = self._postgres_health(params)
            elif engine == "mysql":
                data = self._mysql_health(params)
            else:
                data = self._oracle_health(params)
        except PluginValidationError:
            raise
        except Exception as exc:
            data = {"engine": engine, "checks": {}, "healthy": False, "error": str(exc)}
            data["latency_ms"] = round((time.monotonic() - started) * 1000, 3)
            return self._format(data, params)
        data["healthy"] = self._health_predicate(data)
        data["latency_ms"] = round((time.monotonic() - started) * 1000, 3)
        return self._format(data, params)

    def _sqlite_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        database = Path(str(self._sqlite_path(params))).expanduser()
        checks = self._checks(params)
        data: Dict[str, Any] = {"engine": "sqlite", "database": str(database), "checks": {}}
        uri = f"file:{database}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=float(params.get("timeout", 5))) as conn:
            data["checks"]["connect"] = True
            if "select" in checks:
                data["checks"]["select"] = conn.execute("SELECT 1").fetchone()[0] == 1
            if "version" in checks:
                data["version"] = conn.execute("SELECT sqlite_version()").fetchone()[0]
            if "integrity" in checks:
                data["integrity"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
        return data

    def _postgres_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import psycopg
        except ImportError as exc:
            raise PluginValidationError("install optional dependency: automax[postgres]") from exc
        connection = params.get("connection", {}) or {}
        kwargs = {key: connection[key] for key in ("host", "port", "user", "password") if connection.get(key) is not None}
        if connection.get("dsn"):
            connect_args = (connection["dsn"],)
        else:
            connect_args = ()
            kwargs["dbname"] = connection.get("database", connection.get("dbname"))
        data: Dict[str, Any] = {"engine": "postgres", "checks": {}}
        with psycopg.connect(*connect_args, connect_timeout=float(params.get("timeout", 5)), **kwargs) as conn:
            with conn.cursor() as cursor:
                data["checks"]["connect"] = True
                if "select" in self._checks(params):
                    cursor.execute("SELECT 1")
                    data["checks"]["select"] = cursor.fetchone()[0] == 1
                if "version" in self._checks(params):
                    cursor.execute("SHOW server_version")
                    data["version"] = cursor.fetchone()[0]
                if "read_only" in self._checks(params):
                    cursor.execute("SHOW transaction_read_only")
                    data["read_only"] = cursor.fetchone()[0]
                if "recovery" in self._checks(params):
                    cursor.execute("SELECT pg_is_in_recovery()")
                    data["recovery"] = bool(cursor.fetchone()[0])
        return data

    def _mysql_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import pymysql
        except ImportError as exc:
            raise PluginValidationError("install optional dependency: automax[mysql]") from exc
        connection = params.get("connection", {}) or {}
        data: Dict[str, Any] = {"engine": "mysql", "checks": {}}
        conn = pymysql.connect(
            host=connection.get("host", "localhost"),
            port=int(connection.get("port", 3306)),
            user=connection.get("user"),
            password=connection.get("password"),
            database=connection.get("database"),
            connect_timeout=int(params.get("timeout", 5)),
        )
        try:
            with conn.cursor() as cursor:
                data["checks"]["connect"] = True
                if "select" in self._checks(params):
                    cursor.execute("SELECT 1")
                    data["checks"]["select"] = cursor.fetchone()[0] == 1
                if "version" in self._checks(params):
                    cursor.execute("SELECT VERSION()")
                    data["version"] = cursor.fetchone()[0]
                if "read_only" in self._checks(params):
                    cursor.execute("SELECT @@read_only")
                    data["read_only"] = bool(cursor.fetchone()[0])
        finally:
            conn.close()
        return data

    def _oracle_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import oracledb
        except ImportError as exc:
            raise PluginValidationError("install optional dependency: automax[oracle]") from exc
        connection = params.get("connection", {}) or {}
        data: Dict[str, Any] = {"engine": "oracle", "checks": {}}
        with oracledb.connect(
            user=connection.get("user"),
            password=connection.get("password"),
            dsn=connection.get("dsn"),
        ) as conn:
            with conn.cursor() as cursor:
                data["checks"]["connect"] = True
                if "select" in self._checks(params):
                    cursor.execute("SELECT 1 FROM dual")
                    data["checks"]["select"] = cursor.fetchone()[0] == 1
                if "version" in self._checks(params):
                    data["version"] = conn.version
        return data


class _DatabaseEngineCheckPlugin(DbHealthPlugin):
    engine = ""
    required_params: tuple[str, ...] = ()
    optional_params = (*DbHealthPlugin.optional_params, "engine")

    def _params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        copied = dict(params)
        copied["engine"] = self.engine
        return copied

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(self._params(params))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return super().manual_commands(self._params(params), context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        result = super().execute(self._params(params), context)
        if not result.ok and result.message == "db.health failed":
            result.message = f"{self.name} failed"
        return result


class DatabaseSqliteCheckPlugin(_DatabaseEngineCheckPlugin):
    name = "database.sqlite.check"
    description = "Run read-only controller-side SQLite health checks."
    engine = "sqlite"


class DatabasePostgresCheckPlugin(_DatabaseEngineCheckPlugin):
    name = "database.postgres.check"
    description = "Run read-only controller-side PostgreSQL health checks."
    engine = "postgres"


class DatabaseMysqlCheckPlugin(_DatabaseEngineCheckPlugin):
    name = "database.mysql.check"
    description = "Run read-only controller-side MySQL health checks."
    engine = "mysql"


class DatabaseOracleCheckPlugin(_DatabaseEngineCheckPlugin):
    name = "database.oracle.check"
    description = "Run read-only controller-side Oracle health checks."
    engine = "oracle"
