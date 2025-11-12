"""
Tests for ODBC Database Operations plugin.
"""

from unittest.mock import MagicMock, patch

import pyodbc
import pytest

from automax.core.exceptions import AutomaxError
from automax.plugins.database_operations import (
    check_db_connection,
    execute_db_query,
    get_odbc_data_sources,
    get_odbc_drivers,
)


class TestDatabaseOperationsPlugin:
    """
    Test cases for ODBC Database Operations plugin.
    """

    def test_execute_db_query_missing_connection_string(self):
        """
        Test query execution without connection_string.
        """
        config = {"query": "SELECT 1"}

        with pytest.raises(AutomaxError, match="connection_string is required"):
            execute_db_query(config)

    def test_execute_db_query_missing_query(self):
        """
        Test query execution without query.
        """
        config = {"connection_string": "DRIVER={Test};SERVER=localhost"}

        with pytest.raises(AutomaxError, match="query is required"):
            execute_db_query(config)

    @patch("automax.plugins.database_operations.pyodbc.connect")
    def test_execute_db_query_select(self, mock_connect):
        """
        Test ODBC SELECT query execution.
        """
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "test_user"), (2, "another_user")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        config = {
            "connection_string": "DRIVER={Test};SERVER=localhost;DATABASE=testdb",
            "query": "SELECT * FROM users",
            "fetch": "all",
        }

        result = execute_db_query(config)

        expected = [{"id": 1, "name": "test_user"}, {"id": 2, "name": "another_user"}]
        assert result == expected
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users", {})

    @patch("automax.plugins.database_operations.pyodbc.connect")
    def test_execute_db_query_insert(self, mock_connect):
        """
        Test ODBC INSERT query execution.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        config = {
            "connection_string": "DRIVER={Test};SERVER=localhost;DATABASE=testdb",
            "query": "INSERT INTO users (name) VALUES (?)",
            "parameters": ["test_user"],
            "fetch": "none",
        }

        result = execute_db_query(config)

        assert result == 1
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO users (name) VALUES (?)", ["test_user"]
        )
        mock_conn.commit.assert_called_once()

    @patch("automax.plugins.database_operations.pyodbc.connect")
    def test_execute_db_query_connection_error(self, mock_connect):
        """
        Test query execution with connection error.
        """
        mock_connect.side_effect = Exception("Connection failed")

        config = {
            "connection_string": "DRIVER={Test};SERVER=localhost",
            "query": "SELECT 1",
            "fail_fast": True,
        }

        with pytest.raises(AutomaxError, match="Database operation failed"):
            execute_db_query(config)

    @patch("automax.plugins.database_operations.pyodbc.connect")
    def test_execute_db_query_connection_error_no_fail_fast(self, mock_connect):
        """
        Test query execution with connection error and fail_fast=False.
        """
        mock_connect.side_effect = Exception("Connection failed")

        config = {
            "connection_string": "DRIVER={Test};SERVER=localhost",
            "query": "SELECT 1",
            "fail_fast": False,
        }

        result = execute_db_query(config)
        assert result is None

    @patch("automax.plugins.database_operations.pyodbc.connect")
    def test_check_db_connection_success(self, mock_connect):
        """
        Test successful ODBC database connection test.
        """
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        config = {"connection_string": "DRIVER={Test};SERVER=localhost;DATABASE=testdb"}

        result = check_db_connection(config)
        assert result is True
        mock_conn.close.assert_called_once()

    @patch("automax.plugins.database_operations.pyodbc.connect")
    def test_check_db_connection_failure(self, mock_connect):
        """
        Test failed ODBC database connection test.
        """
        mock_connect.side_effect = Exception("Connection failed")

        config = {
            "connection_string": "DRIVER={Test};SERVER=localhost",
            "fail_fast": False,
        }

        result = check_db_connection(config)
        assert result is False

    @patch("automax.plugins.database_operations.pyodbc.drivers")
    def test_get_odbc_drivers(self, mock_drivers):
        """
        Test getting ODBC drivers list.
        """
        mock_drivers.return_value = [
            "ODBC Driver 17 for SQL Server",
            "PostgreSQL Unicode",
            "MySQL ODBC 8.0 Unicode Driver",
        ]

        result = get_odbc_drivers({})

        assert len(result) == 3
        assert "ODBC Driver 17 for SQL Server" in result

    @patch("automax.plugins.database_operations.pyodbc.dataSources")
    def test_get_odbc_data_sources(self, mock_data_sources):
        """
        Test getting ODBC data sources.
        """
        mock_data_sources.return_value = {
            "MySQL_DSN": "MySQL ODBC 8.0 Unicode Driver",
            "PostgreSQL_DSN": "PostgreSQL Unicode",
        }

        result = get_odbc_data_sources({})

        assert len(result) == 2
        assert "MySQL_DSN" in result

    @patch("automax.plugins.database_operations.pyodbc.connect")
    def test_execute_db_query_pyodbc_error(self, mock_connect):
        """
        Test query execution with specific pyodbc error.
        """
        mock_connect.side_effect = pyodbc.Error("ODBC Connection failed")

        config = {
            "connection_string": "DRIVER={Test};SERVER=localhost",
            "query": "SELECT 1",
            "fail_fast": True,
        }

        with pytest.raises(AutomaxError, match="ODBC database operation failed"):
            execute_db_query(config)
