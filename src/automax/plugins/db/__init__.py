# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Database plugins."""

from automax.plugins.db.health import DatabaseMysqlCheckPlugin, DatabaseOracleCheckPlugin, DatabasePostgresCheckPlugin, DatabaseSqliteCheckPlugin
from automax.plugins.db.mysql import DbMysqlQueryPlugin
from automax.plugins.db.oracle import DbOracleQueryPlugin
from automax.plugins.db.postgres import DbPostgresQueryPlugin
from automax.plugins.db.sqlite import DbSqliteQueryPlugin

__all__ = [
    "DatabaseSqliteCheckPlugin",
    "DatabasePostgresCheckPlugin",
    "DatabaseMysqlCheckPlugin",
    "DatabaseOracleCheckPlugin",
    "DbSqliteQueryPlugin",
    "DbPostgresQueryPlugin",
    "DbMysqlQueryPlugin",
    "DbOracleQueryPlugin",
]
