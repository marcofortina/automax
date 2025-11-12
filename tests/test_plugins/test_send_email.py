"""
Tests for the send_email utility.
"""

import pytest

from automax.core.exceptions import AutomaxError


def test_send_email_dry_run(logger, plugin_manager):
    """
    Verify that sending an email in dry-run mode completes without error.
    """
    send_email = plugin_manager.get_plugin("send_email")
    send_email(
        "smtp.example.com",
        587,
        "from@example.com",
        "to@example.com",
        "Test",
        "Body",
        dry_run=True,
        logger=logger,
    )
    # No exception expected


def test_send_email_failure(logger, plugin_manager):
    """
    Verify that invalid email parameters raise AutomaxError.
    """
    send_email = plugin_manager.get_plugin("send_email")
    with pytest.raises(AutomaxError):
        send_email("invalid", 0, "from", "to", "subj", "body", fail_fast=True)


def test_schema_loaded(plugin_manager):
    """
    Verify SCHEMA is loaded.
    """
    schema = plugin_manager.get_schema("send_email")
    assert "smtp_server" in schema
