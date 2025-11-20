"""
Tests for ssh_command plugin.
"""

import socket
from unittest.mock import ANY, MagicMock, patch

import paramiko
import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestSSHCommandPlugin:
    """
    Test suite for ssh_command plugin.
    """

    def test_ssh_command_plugin_registered(self):
        """
        Verify that ssh_command plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "ssh_command" in global_registry.list_plugins()

        # Verify metadata
        metadata = global_registry.get_metadata("ssh_command")
        assert metadata.name == "ssh_command"
        assert metadata.version == "2.0.0"
        assert "ssh" in metadata.tags
        assert "host" in metadata.required_config
        assert "command" in metadata.required_config
        assert "port" in metadata.optional_config

    def test_ssh_command_plugin_instantiation(self):
        """
        Verify ssh_command plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        config = {
            "host": "example.com",
            "command": "ls -la",
            "port": 22,
            "username": "user",
            "timeout": 30,
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_ssh_command_plugin_configuration_validation(self):
        """
        Verify ssh_command plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class({"host": "example.com"})  # missing command
        assert "required configuration" in str(exc_info.value).lower()

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_execution_success(self, mock_ssh_client):
        """
        Test ssh_command plugin execution with successful command.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_stdout.read.return_value = b"file1.txt\nfile2.txt"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "ls -la",
                "port": 22,
                "username": "user",
                "timeout": 30,
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["host"] == "example.com"
        assert result["port"] == 22
        assert result["command"] == "ls -la"
        assert result["exit_code"] == 0
        assert result["stdout"] == "file1.txt\nfile2.txt"
        assert result["stderr"] == ""

        # Verify mock calls
        mock_ssh_client.assert_called_once()
        mock_client.set_missing_host_key_policy.assert_called_once_with(ANY)
        # Verify that it was called with an AutoAddPolicy instance
        call_args = mock_client.set_missing_host_key_policy.call_args[0]
        assert isinstance(call_args[0], paramiko.AutoAddPolicy)
        mock_client.connect.assert_called_once_with(
            hostname="example.com", port=22, username="user", timeout=30
        )
        mock_client.exec_command.assert_called_once_with("ls -la", timeout=30)
        mock_client.close.assert_called_once()

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_execution_failure(self, mock_ssh_client):
        """
        Test ssh_command plugin execution with command failure.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"command not found"
        mock_stdout.channel.recv_exit_status.return_value = 127

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "invalid_command",
                "port": 22,
                "username": "user",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "failure"
        assert result["host"] == "example.com"
        assert result["command"] == "invalid_command"
        assert result["exit_code"] == 127
        assert result["stdout"] == ""
        assert result["stderr"] == "command not found"

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_authentication_failure(self, mock_ssh_client):
        """
        Test ssh_command plugin execution with authentication failure.
        """
        # Setup mock to raise authentication exception
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect.side_effect = paramiko.AuthenticationException(
            "Auth failed"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "ls -la",
                "username": "user",
                "password": "wrongpass",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "SSH authentication failed" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_with_password(self, mock_ssh_client):
        """
        Test ssh_command plugin execution with password authentication.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_stdout.read.return_value = b"success"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "whoami",
                "username": "user",
                "password": "mypassword",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["host"] == "example.com"
        assert result["port"] == 22
        assert result["command"] == "whoami"
        assert result["exit_code"] == 0
        assert result["stdout"] == "success"
        assert result["stderr"] == ""

        # Verify password was passed to connect
        mock_client.set_missing_host_key_policy.assert_called_once_with(ANY)
        mock_client.connect.assert_called_once_with(
            hostname="example.com",
            port=22,
            username="user",
            timeout=30,
            password="mypassword",
        )

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_with_key_file(self, mock_ssh_client):
        """
        Test ssh_command plugin execution with key file authentication.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_stdout.read.return_value = b"success"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "whoami",
                "username": "user",
                "key_file": "/path/to/key.pem",
            }
        )

        result = plugin.execute()

        # Verify result structure
        assert result["status"] == "success"
        assert result["host"] == "example.com"
        assert result["port"] == 22
        assert result["command"] == "whoami"
        assert result["exit_code"] == 0
        assert result["stdout"] == "success"
        assert result["stderr"] == ""

        # Verify key file was passed to connect
        mock_client.set_missing_host_key_policy.assert_called_once_with(ANY)
        mock_client.connect.assert_called_once_with(
            hostname="example.com",
            port=22,
            username="user",
            timeout=30,
            key_filename="/path/to/key.pem",
        )


class TestSSHCommandErrorHandling:
    """
    Additional test suite for SSH Command error scenarios.

    These tests complement the existing tests without modifying them.

    """

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_connection_timeout(self, mock_ssh_client):
        """
        Test SSH command plugin execution with connection timeout.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect.side_effect = socket.timeout("Connection timeout")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "ls -la",
                "username": "user",
                "timeout": 5,
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Connection timeout" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_connection_refused(self, mock_ssh_client):
        """
        Test SSH command plugin execution with connection refused.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect.side_effect = ConnectionRefusedError("Connection refused")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "ls -la",
                "username": "user",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Connection refused" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_no_route_to_host(self, mock_ssh_client):
        """
        Test SSH command plugin execution with no route to host.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect.side_effect = OSError("No route to host")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "unreachable.example.com",
                "command": "ls -la",
                "username": "user",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "No route to host" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_invalid_key_file(self, mock_ssh_client):
        """
        Test SSH command plugin execution with invalid key file.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect.side_effect = paramiko.SSHException("Invalid key file")

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "ls -la",
                "username": "user",
                "key_file": "/invalid/key.pem",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Invalid key file" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_command_timeout(self, mock_ssh_client):
        """
        Test SSH command plugin execution with command timeout.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_stdout.channel.recv_exit_status.side_effect = socket.timeout(
            "Command timeout"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "sleep 30",
                "username": "user",
                "timeout": 5,
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Command timeout" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_ssh_command_plugin_channel_error(self, mock_ssh_client):
        """
        Test SSH command plugin execution with channel error.
        """
        # Setup mocks
        mock_client = MagicMock()
        mock_ssh_client.return_value = mock_client

        mock_client.exec_command.side_effect = paramiko.ChannelException(
            1, "Channel error"
        )

        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("ssh_command")
        plugin = plugin_class(
            {
                "host": "example.com",
                "command": "ls -la",
                "username": "user",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Channel error" in str(exc_info.value)
