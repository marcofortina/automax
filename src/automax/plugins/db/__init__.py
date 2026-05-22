"""Database plugins."""

from automax.plugins.db.mysql import DbMysqlQueryPlugin
from automax.plugins.db.oracle import DbOracleQueryPlugin
from automax.plugins.db.postgres import DbPostgresQueryPlugin
from automax.plugins.db.sqlite import DbSqliteQueryPlugin

__all__ = [
    "DbSqliteQueryPlugin",
    "DbPostgresQueryPlugin",
    "DbMysqlQueryPlugin",
    "DbOracleQueryPlugin",
]
