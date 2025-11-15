"""
Plugin for performing database operations.
"""

import sqlite3
from typing import Any, Dict, List

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class DatabaseOperationsPlugin(BasePlugin):
    """
    Perform operations on databases.
    """

    METADATA = PluginMetadata(
        name="database_operations",
        version="2.0.0",
        description="Perform operations on databases",
        author="Automax Team",
        category="database",
        tags=["database", "sql", "query"],
        required_config=["database_type", "query"],
        optional_config=[
            "host",
            "port",
            "username",
            "password",
            "database",
            "parameters",
        ],
    )

    SCHEMA = {
        "database_type": {"type": str, "required": True},
        "query": {"type": str, "required": True},
        "host": {"type": str, "required": False},
        "port": {"type": int, "required": False},
        "username": {"type": str, "required": False},
        "password": {"type": str, "required": False},
        "database": {"type": str, "required": False},
        "parameters": {"type": dict, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute a database query.

        Returns:
            Dictionary containing query results.

        Raises:
            PluginExecutionError: If the query fails.

        """
        database_type = self.config["database_type"]
        query = self.config["query"]
        parameters = self.config.get("parameters", [])

        self.logger.info(f"Executing {database_type} query: {query}")

        try:
            if database_type == "sqlite":
                result = self._execute_sqlite(query, parameters)
            else:
                raise PluginExecutionError(
                    f"Unsupported database type: {database_type}"
                )

            self.logger.info(
                f"Successfully executed query, affected rows: {result.get('row_count', 0)}"
            )
            return result

        except Exception as e:
            error_msg = f"Database operation failed: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

    def _execute_sqlite(self, query: str, parameters: List[Any]) -> Dict[str, Any]:
        """
        Execute a SQLite query.
        """
        database_path = self.config.get("database", ":memory:")

        try:
            with sqlite3.connect(database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, parameters)

                if query.strip().lower().startswith("select"):
                    rows = cursor.fetchall()
                    result = {
                        "database_type": "sqlite",
                        "query": query,
                        "rows": [dict(row) for row in rows],
                        "row_count": len(rows),
                        "status": "success",
                    }
                else:
                    result = {
                        "database_type": "sqlite",
                        "query": query,
                        "row_count": cursor.rowcount,
                        "lastrowid": cursor.lastrowid,
                        "status": "success",
                    }

                conn.commit()
                return result

        except sqlite3.Error as e:
            raise PluginExecutionError(f"SQLite error: {e}") from e
