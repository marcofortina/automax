"""
Tests for database_operations plugin.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestDatabaseOperationsPlugin:
    """
    Test suite for database_operations plugin.
    """

    def test_database_operations_plugin_registered(self):
        """
        Verify that database_operations plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "database_operations" in global_registry.list_plugins()

        # Verify metadata matches the updated plugin
        metadata = global_registry.get_metadata("database_operations")
        assert metadata.name == "database_operations"
        assert metadata.version == "2.0.0"
        assert "database" in metadata.tags
        assert "sql" in metadata.tags
        assert "connection_string" in metadata.required_config
        assert "query" in metadata.required_config
        assert "action" in metadata.required_config

    def test_database_operations_plugin_instantiation(self):
        """
        Verify database_operations plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        config = {
            "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
            "query": "SELECT * FROM users",
            "action": "select",
            "parameters": [1, 2],
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_database_operations_plugin_configuration_validation(self):
        """
        Verify database_operations plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"connection_string": "DRIVER={SQL Server};"})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("pyodbc.connect")
    def test_database_operations_plugin_select_query(self, mock_connect):
        """
        Test database_operations plugin execution with SELECT query.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock cursor description and data for SELECT
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "John Doe"), (2, "Jane Smith")]

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "SELECT * FROM users",
                "action": "select",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["query"] == "SELECT * FROM users"
        assert result["columns"] == ["id", "name"]
        assert result["rows"] == [(1, "John Doe"), (2, "Jane Smith")]
        assert result["row_count"] == 2

        # Verify mock calls
        mock_connect.assert_called_once_with(
            "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;"
        )
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users", [])

    @patch("pyodbc.connect")
    def test_database_operations_plugin_select_with_parameters(self, mock_connect):
        """
        Test database_operations plugin SELECT query with parameters.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "John Doe")]

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "SELECT * FROM users WHERE id = ? AND active = ?",
                "action": "select",
                "parameters": [1, 1],
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["row_count"] == 1

        # Verify mock calls with parameters
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM users WHERE id = ? AND active = ?", [1, 1]
        )

    @patch("pyodbc.connect")
    def test_database_operations_plugin_insert_query(self, mock_connect):
        """
        Test database_operations plugin execution with INSERT query.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 100

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "INSERT INTO users (name, email) VALUES (?, ?)",
                "action": "insert",
                "parameters": ["John Doe", "john@example.com"],
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["query"] == "INSERT INTO users (name, email) VALUES (?, ?)"
        assert result["row_count"] == 1
        assert result["lastrowid"] == 100

        # Verify mock calls
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ["John Doe", "john@example.com"],
        )
        mock_conn.commit.assert_called_once()

    @patch("pyodbc.connect")
    def test_database_operations_plugin_update_query(self, mock_connect):
        """
        Test database_operations plugin execution with UPDATE query.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 5
        mock_cursor.lastrowid = None

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "UPDATE users SET active = ? WHERE age > ?",
                "action": "update",
                "parameters": [1, 18],
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["row_count"] == 5
        assert result["lastrowid"] is None

        # Verify mock calls
        mock_cursor.execute.assert_called_once_with(
            "UPDATE users SET active = ? WHERE age > ?", [1, 18]
        )
        mock_conn.commit.assert_called_once()

    @patch("pyodbc.connect")
    def test_database_operations_plugin_delete_query(self, mock_connect):
        """
        Test database_operations plugin execution with DELETE query.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 3

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "DELETE FROM users WHERE inactive = 1",
                "action": "delete",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["row_count"] == 3

        # Verify mock calls
        mock_cursor.execute.assert_called_once_with(
            "DELETE FROM users WHERE inactive = 1", []
        )
        mock_conn.commit.assert_called_once()

    @patch("pyodbc.connect")
    def test_database_operations_plugin_execute_action(self, mock_connect):
        """
        Test database_operations plugin execution with execute action.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = -1  # Typical for DDL statements

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "CREATE TABLE new_table (id INT, name VARCHAR(255))",
                "action": "execute",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["row_count"] == -1

        # Verify mock calls
        mock_cursor.execute.assert_called_once_with(
            "CREATE TABLE new_table (id INT, name VARCHAR(255))", []
        )
        mock_conn.commit.assert_called_once()

    @patch("pyodbc.connect")
    def test_database_operations_plugin_select_with_no_columns(self, mock_connect):
        """
        Test database_operations plugin SELECT query with no columns (empty result).
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock empty result
        mock_cursor.description = None
        mock_cursor.fetchall.return_value = []

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "SELECT * FROM empty_table",
                "action": "select",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["columns"] == []
        assert result["rows"] == []
        assert result["row_count"] == 0

    @patch("pyodbc.connect")
    def test_database_operations_plugin_database_error(self, mock_connect):
        """
        Test database_operations plugin execution with database error.
        """
        # Setup mocks to raise exception
        mock_connect.side_effect = Exception("Connection failed")

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=invalid;DATABASE=test;",
                "query": "SELECT * FROM users",
                "action": "select",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Database execution error" in str(exc_info.value)

    @patch("pyodbc.connect")
    def test_database_operations_plugin_select_fetch_error(self, mock_connect):
        """
        Test database_operations plugin SELECT query with fetch error.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock fetchall to raise exception
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.side_effect = Exception("Fetch error")

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "SELECT * FROM users",
                "action": "select",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        # Verify PluginExecutionError is raised and contains original message
        assert isinstance(exc_info.value, PluginExecutionError)
        assert "Fetch error" in str(exc_info.value)

    @patch("pyodbc.connect")
    def test_database_operations_plugin_insert_commit_error(self, mock_connect):
        """
        Test database_operations plugin INSERT query with commit error.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit.side_effect = Exception("Commit failed")

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "INSERT INTO users (name) VALUES (?)",
                "action": "insert",
                "parameters": ["John"],
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        # Verify PluginExecutionError is raised and contains original message
        assert isinstance(exc_info.value, PluginExecutionError)
        assert "Commit failed" in str(exc_info.value)

    def test_database_operations_plugin_invalid_action(self):
        """
        Test database_operations plugin with invalid action.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                "query": "SELECT * FROM users",
                "action": "invalid_action",  # invalid action
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Invalid action 'invalid_action'" in str(exc_info.value)

    def test_database_operations_plugin_pyodbc_not_installed(self):
        """
        Test database_operations plugin when pyodbc is not installed.
        """
        # Temporarily simulate pyodbc not being available
        import automax.plugins.database_operations as db_module

        original_available = db_module.PYODBC_AVAILABLE
        db_module.PYODBC_AVAILABLE = False

        try:
            global_registry.load_all_plugins()

            plugin_class = global_registry.get_plugin_class("database_operations")
            plugin = plugin_class(
                {
                    "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;",
                    "query": "SELECT * FROM users",
                    "action": "select",
                }
            )

            with pytest.raises(PluginExecutionError) as exc_info:
                plugin.execute()

            assert "pyodbc not installed" in str(exc_info.value)
        finally:
            # Restore original value
            db_module.PYODBC_AVAILABLE = original_available
