"""
Tests for send_email plugin.
"""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from automax.plugins.exceptions import PluginExecutionError
from automax.plugins.registry import global_registry


class TestSendEmailPlugin:
    """
    Test suite for send_email plugin.
    """

    def test_send_email_plugin_registered(self):
        """
        Verify that send_email plugin is properly registered.
        """
        global_registry.load_all_plugins()
        assert "send_email" in global_registry.list_plugins()

        metadata = global_registry.get_metadata("send_email")
        assert metadata.name == "send_email"
        assert "email" in metadata.tags
        assert "smtp_server" in metadata.required_config
        assert "port" in metadata.required_config
        assert "username" in metadata.required_config
        assert "password" in metadata.required_config
        assert "to" in metadata.required_config
        assert "subject" in metadata.required_config
        assert "body" in metadata.required_config

    def test_send_email_plugin_instantiation(self):
        """
        Verify send_email plugin can be instantiated with config.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("send_email")
        config = {
            "smtp_server": "smtp.gmail.com",
            "port": 587,
            "username": "user@gmail.com",
            "password": "app-password",
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "This is a test email",
            "from_addr": "sender@gmail.com",
            "cc": ["cc@example.com"],
            "is_html": True,
        }

        plugin_instance = plugin_class(config)
        assert plugin_instance is not None
        assert plugin_instance.config == config

    def test_send_email_plugin_configuration_validation(self):
        """
        Verify send_email plugin configuration validation.
        """
        global_registry.load_all_plugins()

        plugin_class = global_registry.get_plugin_class("send_email")

        # Test with missing required configuration
        with pytest.raises(Exception) as exc_info:
            plugin_class(
                {
                    "smtp_server": "smtp.gmail.com",
                    "port": 587,
                    "username": "user@gmail.com",
                    "password": "app-password",
                    "to": "recipient@example.com",
                    "subject": "Test Email",
                    # missing body
                }
            )
        assert "required configuration" in str(exc_info.value).lower()

    @patch("smtplib.SMTP")
    def test_send_email_plugin_execution_success(self, mock_smtp):
        """
        Test send_email plugin execution with successful email send.
        """
        # Setup mocks
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("send_email")
        plugin = plugin_class(
            {
                "smtp_server": "smtp.example.com",
                "port": 587,
                "username": "user@example.com",
                "password": "password123",
                "to": "recipient@example.com",
                "subject": "Test Email",
                "body": "This is a test email",
                "from_addr": "sender@example.com",
            }
        )

        result = plugin.execute()

        assert result["status"] == "success"
        assert result["smtp_server"] == "smtp.example.com"
        assert result["port"] == 587
        assert result["from"] == "sender@example.com"
        assert result["to"] == "recipient@example.com"
        assert result["subject"] == "Test Email"

        # Verify SMTP calls
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password123")
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_plugin_multiple_recipients(self, mock_smtp):
        """
        Test send_email plugin execution with multiple recipients.
        """
        # Setup mocks
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("send_email")
        plugin = plugin_class(
            {
                "smtp_server": "smtp.example.com",
                "port": 587,
                "username": "user@example.com",
                "password": "password123",
                "to": ["recipient1@example.com", "recipient2@example.com"],
                "cc": ["cc1@example.com", "cc2@example.com"],
                "bcc": ["bcc@example.com"],
                "subject": "Test Email",
                "body": "This is a test email",
                "from_addr": "sender@example.com",
            }
        )

        result = plugin.execute()

        assert result["status"] == "success"
        assert result["to"] == [
            "recipient1@example.com",
            "recipient2@example.com",
            "cc1@example.com",
            "cc2@example.com",
            "bcc@example.com",
        ]

        # Verify SMTP calls
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password123")
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_plugin_html_email(self, mock_smtp):
        """
        Test send_email plugin execution with HTML email.
        """
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=None)

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("send_email")
        plugin = plugin_class(
            {
                "smtp_server": "smtp.example.com",
                "port": 587,
                "username": "user@example.com",
                "password": "app-password",
                "to": "recipient@example.com",
                "subject": "Test HTML Email",
                "body": "<h1>Hello</h1><p>This is HTML</p>",
                "is_html": True,
            }
        )

        result = plugin.execute()

        assert result["status"] == "success"

        # Verify SMTP calls
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_plugin_smtp_exception(self, mock_smtp):
        """
        Test send_email plugin execution with SMTP exception.
        """
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=None)
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("send_email")
        plugin = plugin_class(
            {
                "smtp_server": "smtp.example.com",
                "port": 587,
                "username": "user@example.com",
                "password": "wrongpassword",
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "body": "Test Body",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "SMTP error while sending email" in str(exc_info.value)

    @patch("smtplib.SMTP")
    def test_send_email_plugin_general_error(self, mock_smtp):
        """
        Test send_email plugin execution with general error.
        """
        mock_smtp.side_effect = Exception("Network connection failed")

        global_registry.load_all_plugins()
        plugin_class = global_registry.get_plugin_class("send_email")
        plugin = plugin_class(
            {
                "smtp_server": "smtp.gmail.com",
                "port": 587,
                "username": "user@gmail.com",
                "password": "app-password",
                "to": "recipient@example.com",
                "subject": "Test Email",
                "body": "This is a test email",
            }
        )

        with pytest.raises(PluginExecutionError) as exc_info:
            plugin.execute()

        assert "Failed to send email" in str(exc_info.value)
