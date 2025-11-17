"""
Plugin for performing SQL operations using ODBC via pyodbc.
"""

from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError

try:
    import pyodbc

    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False


@register_plugin
class DatabaseOperationsPlugin(BasePlugin):
    """
    Execute SQL queries using any ODBC connection via pyodbc.
    """

    METADATA = PluginMetadata(
        name="database_operations",
        version="2.0.0",
        description="Execute SQL queries via ODBC using pyodbc",
        author="Marco Fortina",
        category="database",
        tags=["database", "sql", "odbc"],
        required_config=["connection_string", "query", "action"],
        optional_config=["parameters"],
    )

    SCHEMA = {
        "connection_string": {"type": str, "required": True},
        "query": {"type": str, "required": True},
        "parameters": {"type": list, "required": False},
        "action": {
            "type": str,
            "required": True,
        },  # select | insert | update | delete | execute
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute an SQL operation using pyodbc.

        Supported actions:
            - select  : fetch rows
            - insert  : commit insert operation
            - update  : commit update operation
            - delete  : commit delete operation
            - execute : run any SQL without expecting result rows

        Returns:
            dict: query, result rows (if select), row_count, lastrowid (if available), status

        Raises:
            PluginExecutionError: if pyodbc is missing or any DB error occurs.

        """
        if not PYODBC_AVAILABLE:
            raise PluginExecutionError(
                "pyodbc not installed. Install with: pip install pyodbc"
            )

        conn_str = self.config["connection_string"]
        query = self.config["query"]
        params = self.config.get("parameters", [])
        action = self.config["action"].lower()

        self.logger.info(f"Database action={action} query={query}")

        valid_actions = {"select", "insert", "update", "delete", "execute"}
        if action not in valid_actions:
            raise PluginExecutionError(
                f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            )

        try:
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()

                self.logger.info("Executing SQL via pyodbc")

                cursor.execute(query, params)

                if action == "select":
                    try:
                        rows = cursor.fetchall()
                        cols = (
                            [column[0] for column in cursor.description]
                            if cursor.description
                            else []
                        )

                        result = {
                            "query": query,
                            "columns": cols,
                            "rows": [tuple(row) for row in rows],
                            "row_count": len(rows),
                            "status": "success",
                        }

                        self.logger.info(
                            f"Successfully executed SELECT returning {len(rows)} rows"
                        )
                        return result

                    except Exception as e:
                        self.logger.error(f"ODBC SELECT error: {e}")
                        raise PluginExecutionError(str(e)) from e

                else:
                    try:
                        row_count = cursor.rowcount
                        lastrowid = getattr(cursor, "lastrowid", None)

                        conn.commit()

                        result = {
                            "query": query,
                            "row_count": row_count,
                            "lastrowid": lastrowid,
                            "status": "success",
                        }

                        self.logger.info(
                            f"Successfully executed {action.upper()} with row_count={row_count}"
                        )
                        return result

                    except Exception as e:
                        self.logger.error(f"ODBC {action} error: {e}")
                        raise PluginExecutionError(str(e)) from e

        except Exception as e:
            self.logger.error(f"ODBC database operation failed: {e}")
            raise PluginExecutionError(f"Database execution error: {e}") from e
