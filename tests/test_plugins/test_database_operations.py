"""
Tests for database_operations plugin.
"""

import sqlite3
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

        # Verify metadata
        metadata = global_registry.get_metadata("database_operations")
        assert metadata.name == "database_operations"
        assert "database" in metadata.tags
        assert "database_type" in metadata.required_config
        assert "query" in metadata.required_config

    def test_database_operations_plugin_instantiation(self):
        """
        Verify database_operations plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        config = {
            "database_type": "sqlite",
            "query": "SELECT * FROM users",
            "database": ":memory:",
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
            plugin_class({"database_type": "sqlite"})

        assert "required configuration" in str(exc_info.value).lower()

    @patch("sqlite3.connect")
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
        mock_conn.row_factory = sqlite3.Row

        # Mock a row with column names
        mock_row = MagicMock()
        mock_row.keys.return_value = ["id", "name"]
        mock_cursor.fetchall.return_value = [mock_row]

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "database_type": "sqlite",
                "database": ":memory:",
                "query": "SELECT * FROM users",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["database_type"] == "sqlite"
        assert result["query"] == "SELECT * FROM users"
        assert result["row_count"] == 1

        # Verify mock call
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users", [])

    @patch("sqlite3.connect")
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
        mock_cursor.lastrowid = 5

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "database_type": "sqlite",
                "database": ":memory:",
                "query": "INSERT INTO users (name) VALUES (?)",
                "parameters": ["John"],
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["row_count"] == 1
        assert result["lastrowid"] == 5

        # Verify mock call
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO users (name) VALUES (?)", ["John"]
        )

    @patch("sqlite3.connect")
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
        mock_cursor.rowcount = 3

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {
                "database_type": "sqlite",
                "database": ":memory:",
                "query": "UPDATE users SET active = ? WHERE age > ?",
                "parameters": [1, 18],
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["row_count"] == 3

        # Verify mock call
        mock_cursor.execute.assert_called_once_with(
            "UPDATE users SET active = ? WHERE age > ?", [1, 18]
        )

    @patch("sqlite3.connect")
    def test_database_operations_plugin_sqlite_error(self, mock_connect):
        """
        Test database_operations plugin execution with SQLite error.
        """
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Setup mock to raise exception
        mock_cursor.execute.side_effect = sqlite3.Error("SQL syntax error")

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {"database_type": "sqlite", "database": ":memory:", "query": "INVALID SQL"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "SQLite error" in str(exc_info.value)

    def test_database_operations_plugin_unsupported_database_type(self):
        """
        Test database_operations plugin with unsupported database type.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("database_operations")
        plugin = plugin_class(
            {"database_type": "postgresql", "query": "SELECT * FROM users"}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Unsupported database type" in str(exc_info.value)
