"""
Tests for common utility functions in Automax.
"""

from automax.core.exceptions import AutomaxError
from automax.core.utils.common_utils import echo


def test_automax_error():
    """
    Verify AutomaxError stores message and level correctly.
    """
    err = AutomaxError("test", level="FATAL")
    assert err.message == "test"
    assert err.level == "FATAL"


def test_echo_logs(caplog):
    """
    Verify echo logs messages at correct level using a dummy logger.
    """

    class DummyLogger:
        def __init__(self):
            self.records = []

        def debug(self, msg):
            self.records.append(("DEBUG", msg))

        def info(self, msg):
            self.records.append(("INFO", msg))

        def warning(self, msg):
            self.records.append(("WARNING", msg))

        def error(self, msg):
            self.records.append(("ERROR", msg))

    logger = DummyLogger()
    echo("info msg", logger, "INFO")
    echo("warn msg", logger, "WARNING")
    echo("error msg", logger, "ERROR")
    echo("debug msg", logger, "DEBUG")

    levels = [r[0] for r in logger.records]
    assert "INFO" in levels
    assert "WARNING" in levels
    assert "ERROR" in levels
    assert "DEBUG" in levels
