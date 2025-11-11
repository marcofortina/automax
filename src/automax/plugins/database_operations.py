"""
Plugin for database operations utility using ODBC.
Provides universal database operations across all ODBC-compatible databases.
"""

from typing import Any, Dict

import pyodbc

from automax.core.exceptions import AutomaxError
from automax.core.utils.common_utils import echo


def execute_db_query(config: Dict[str, Any], logger=None):
    """
    Execute database queries using ODBC driver.

    Supports all ODBC-compatible databases:
    - SQL Server, PostgreSQL, MySQL, Oracle, SQLite, DB2, etc.

    Args:
        config: Configuration dictionary containing:
            - connection_string: ODBC connection string (required)
            - query: SQL query to execute (required)
            - parameters: Query parameters (optional)
            - fetch: Whether to fetch results ('one', 'all', 'none')
            - fail_fast: Whether to raise errors immediately (default: True)
            - timeout: Query timeout in seconds (optional)
        logger: Logger instance for logging

    Returns:
        Query results or affected row count

    Raises:
        AutomaxError: If query execution fails and fail_fast is True
    """
    fail_fast = config.get("fail_fast", True)

    if not config.get("connection_string"):
        msg = "connection_string is required for ODBC database operations"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None

    if not config.get("query"):
        msg = "query is required for database operations"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None

    connection = None
    try:
        # Establish ODBC connection
        timeout = config.get("timeout")
        connection = pyodbc.connect(config["connection_string"], timeout=timeout)
        cursor = connection.cursor()

        # Execute query
        parameters = config.get("parameters", {})
        cursor.execute(config["query"], parameters)

        # Handle results based on fetch type
        fetch_type = config.get("fetch", "none")
        result = _handle_query_results(cursor, fetch_type, config["query"])

        # Commit if not a SELECT query
        if not config["query"].strip().lower().startswith("select"):
            connection.commit()
            if logger:
                echo(
                    f"Executed query successfully: {config['query']}",
                    logger,
                    level="INFO",
                )

        return result

    except pyodbc.Error as e:
        if connection:
            connection.rollback()

        msg = f"ODBC database operation failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None

    except Exception as e:
        if connection:
            connection.rollback()

        msg = f"Database operation failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return None

    finally:
        if connection:
            connection.close()


def _handle_query_results(cursor, fetch_type: str, query: str):
    """Handle query results based on fetch type."""
    query_lower = query.strip().lower()

    if fetch_type == "one":
        row = cursor.fetchone()
        if row:
            # Convert to dictionary if possible
            try:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
            except Exception:
                return row
        return None

    elif fetch_type == "all":
        rows = cursor.fetchall()
        if rows and cursor.description:
            # Convert to list of dictionaries
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return rows

    elif fetch_type == "none":
        if query_lower.startswith(("insert", "update", "delete")):
            return cursor.rowcount
        return None
    else:
        raise AutomaxError(f"Invalid fetch type: {fetch_type}")


def check_db_connection(config: Dict[str, Any], logger=None):
    """
    Test ODBC database connection.

    Args:
        config: Same as execute_db_query configuration
        logger: Logger instance

    Returns:
        bool: True if connection successful, False otherwise
    """
    fail_fast = config.get("fail_fast", True)

    try:
        timeout = config.get("timeout", 5)
        connection = pyodbc.connect(config["connection_string"], timeout=timeout)
        connection.close()

        if logger:
            echo("ODBC database connection test successful", logger, level="INFO")
        return True

    except Exception as e:
        msg = f"ODBC database connection test failed: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        if fail_fast:
            raise AutomaxError(msg, level="FATAL")
        return False


def get_odbc_drivers(config: Dict[str, Any], logger=None):
    """
    Get list of available ODBC drivers on the system.

    Args:
        config: Empty dict or configuration (not used)
        logger: Logger instance

    Returns:
        List of available ODBC driver names
    """
    try:
        drivers = pyodbc.drivers()
        if logger:
            echo(f"Found {len(drivers)} ODBC drivers", logger, level="INFO")
        return drivers

    except Exception as e:
        msg = f"Failed to get ODBC drivers: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        return []


def get_odbc_data_sources(config: Dict[str, Any], logger=None):
    """
    Get list of available ODBC data sources on the system.

    Args:
        config: Empty dict or configuration (not used)
        logger: Logger instance

    Returns:
        Dictionary of available data sources
    """
    try:
        data_sources = pyodbc.dataSources()
        if logger:
            echo(f"Found {len(data_sources)} ODBC data sources", logger, level="INFO")
        return data_sources

    except Exception as e:
        msg = f"Failed to get ODBC data sources: {e}"
        if logger:
            echo(msg, logger, level="ERROR")
        return {}


REGISTER_UTILITIES = [
    ("execute_db_query", execute_db_query),
    ("check_db_connection", check_db_connection),
    ("get_odbc_drivers", get_odbc_drivers),
    ("get_odbc_data_sources", get_odbc_data_sources),
]

SCHEMA = {
    "connection_string": {"type": str, "required": True},
    "query": {"type": str, "required": True},
    "parameters": {"type": dict, "required": False, "default": {}},
    "fetch": {
        "type": str,
        "required": False,
        "options": ["one", "all", "none"],
        "default": "none",
    },
    "fail_fast": {"type": bool, "default": True},
    "timeout": {"type": int, "required": False},
}
