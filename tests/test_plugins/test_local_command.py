"""
Tests for local_command plugin.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestLocalCommandPlugin:
    """
    Test suite for local_command plugin.
    """

    def test_local_command_plugin_registered(self):
        """
        Verify that local_command plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "local_command" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("local_command")
        assert metadata.name == "local_command"
        assert metadata.version == "2.0.0"
        assert "command" in metadata.tags
        assert "command" in metadata.required_config
        assert "timeout" in metadata.optional_config

    def test_local_command_plugin_instantiation(self):
        """
        Verify local_command plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        config = {"command": "echo 'test'", "timeout": 30, "shell": True, "cwd": "/tmp"}

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_local_command_plugin_configuration_validation(self):
        """
        Verify local_command plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({})
        assert "required configuration" in str(exc_info.value).lower()

    @patch("subprocess.run")
    def test_local_command_plugin_execution_success(self, mock_run):
        """
        Test local_command plugin execution with successful command.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class({"command": "echo 'test'", "timeout": 30, "shell": True})

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["command"] == "echo 'test'"
        assert result["returncode"] == 0
        assert result["stdout"] == "test output"
        assert result["stderr"] == ""
        assert result["timeout"] == 30
        assert result["shell"] is True

        # Verify mock call
        mock_run.assert_called_once_with(
            "echo 'test'",
            shell=True,
            timeout=30,
            cwd=None,
            env=None,
            input=None,
            capture_output=True,
            text=True,
            encoding=None,
        )

    @patch("subprocess.run")
    def test_local_command_plugin_execution_failure(self, mock_run):
        """
        Test local_command plugin execution with command failure.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "command not found"
        mock_run.return_value = mock_result

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class(
            {"command": "invalid_command", "timeout": 30, "shell": True}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "failure"
        assert result["command"] == "invalid_command"
        assert result["returncode"] == 1
        assert result["stdout"] == ""
        assert result["stderr"] == "command not found"

    @patch("subprocess.run")
    def test_local_command_plugin_execution_timeout(self, mock_run):
        """
        Test local_command plugin execution with timeout.
        """
        # Setup mock to raise TimeoutExpired
        mock_run.side_effect = subprocess.TimeoutExpired("echo 'test'", timeout=30)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class({"command": "echo 'test'", "timeout": 30, "shell": True})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Command timed out after 30 seconds" in str(exc_info.value)

    @patch("subprocess.run")
    def test_local_command_plugin_execution_command_not_found(self, mock_run):
        """
        Test local_command plugin execution with command not found.
        """
        # Setup mock to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("Command not found")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class(
            {"command": "nonexistent_command", "timeout": 30, "shell": True}
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Command not found" in str(exc_info.value)

    @patch("subprocess.run")
    def test_local_command_plugin_execution_with_input(self, mock_run):
        """
        Test local_command plugin execution with input data.
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class(
            {"command": "cat", "input_data": "test input", "timeout": 30, "shell": True}
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["command"] == "cat"
        assert result["returncode"] == 0

        # Verify mock call
        mock_run.assert_called_once_with(
            "cat",
            shell=True,
            timeout=30,
            cwd=None,
            env=None,
            input="test input",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )


class TestLocalCommandErrorHandling:
    """
    Additional test suite for Local Command error scenarios.

    These tests complement the existing tests without modifying them.

    """

    @patch("subprocess.run")
    def test_local_command_plugin_permission_denied(self, mock_run):
        """
        Test local_command plugin execution with permission denied.
        """
        # Setup mock to raise permission error
        mock_run.side_effect = PermissionError("Permission denied")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class({"command": "rm /root/file", "shell": True})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Permission denied" in str(exc_info.value)

    @patch("subprocess.run")
    def test_local_command_plugin_invalid_working_directory(self, mock_run):
        """
        Test local_command plugin execution with invalid working directory.
        """
        # Setup mock to raise file not found error for working directory
        mock_run.side_effect = FileNotFoundError("No such file or directory")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class({"command": "ls", "cwd": "/invalid/directory"})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Command not found" in str(exc_info.value)

    @patch("subprocess.run")
    def test_local_command_plugin_invalid_environment(self, mock_run):
        """
        Test local_command plugin execution with invalid environment variables.
        """
        # Setup mock to raise exception for invalid env
        mock_run.side_effect = Exception("Invalid environment")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class({"command": "echo $TEST", "env": {"INVALID_VAR": None}})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Failed to execute command" in str(exc_info.value)
        assert "Invalid environment" in str(exc_info.value)

    @patch("subprocess.run")
    def test_local_command_plugin_process_error(self, mock_run):
        """
        Test local_command plugin execution with process error.
        """
        # Setup mock to raise general process error
        mock_run.side_effect = Exception("Process error")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("local_command")
        plugin = plugin_class({"command": "invalid_command", "shell": True})

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Process error" in str(exc_info.value)
