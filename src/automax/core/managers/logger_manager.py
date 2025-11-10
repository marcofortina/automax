"""
Logger manager for Automax.

Handles centralized logging to console, file, optional JSON, and error file.
"""

import atexit
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Logger name constant
LOGGER_NAME = "automax"

# Mapping of levels to aligned strings for console/file logs
LEVEL_MAP = {
    "DEBUG": "DEBUG",
    "INFO": "INFO ",
    "WARN": "WARN ",
    "WARNING": "WARN ",
    "ERROR": "ERROR",
    "FATAL": "FATAL",
    "CRITICAL": "FATAL",
}


class AlignedFormatter(logging.Formatter):
    """
    Formatter that aligns level names and formats timestamps in ISO 8601 with local timezone.
    """

    def formatTime(self, record, datefmt=None):
        # Convert timestamp to ISO 8601 with local timezone and milliseconds
        dt = datetime.fromtimestamp(record.created).astimezone()
        return dt.isoformat(timespec="milliseconds")

    def format(self, record):
        # Align level name for console/file logs
        record.levelname = LEVEL_MAP.get(record.levelname, record.levelname).ljust(5)
        return super().format(record)


class JsonStreamingFormatter(logging.Formatter):
    """
    Formatter that outputs log records as JSON objects compliant with RFC 8259.
    """

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created)
            .astimezone()
            .isoformat(timespec="milliseconds"),
            "level": logging.getLevelName(record.levelno).upper(),
            "message": record.getMessage(),
        }
        # Always add trailing comma
        return json.dumps(log_entry, ensure_ascii=False) + ","


class LoggerManager:
    """
    Manager class for centralized logging.
    """

    def __init__(self, log_directory=None, log_level="DEBUG", json_log=False):
        """
        Initialize LoggerManager.

        Args:
            log_directory (str or Path, optional): Directory for log files.
            log_level (str): Logging level.
            json_log (bool): Enable JSON logging.
        """
        self.log_directory = Path(log_directory) if log_directory else Path("logs")
        self.log_directory.mkdir(parents=True, exist_ok=True)
        self.log_level = getattr(logging, log_level.upper(), logging.DEBUG)
        self.json_log = json_log
        self._logger_initialized = False

        self._setup_logger()

    @property
    def logger(self):
        return self._logger

    def _setup_logger(self):
        if self._logger_initialized:
            return

        # Generate timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_directory / f"{LOGGER_NAME}_{timestamp}.log"
        self.error_file = self.log_directory / f"{LOGGER_NAME}_{timestamp}.err"
        self.json_file = (
            self.log_directory / f"{LOGGER_NAME}_{timestamp}.json"
            if self.json_log
            else None
        )

        # Initialize logger
        self._logger = logging.getLogger(LOGGER_NAME)
        self._logger.setLevel(self.log_level)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            AlignedFormatter("%(asctime)s [ %(levelname)s ]  %(message)s")
        )
        self._logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(
            AlignedFormatter("%(asctime)s [ %(levelname)s ]  %(message)s")
        )
        self._logger.addHandler(file_handler)

        # JSON handler (if enabled)
        self.json_handler = None
        if self.json_log:
            self.json_handler = logging.FileHandler(self.json_file, mode="w")
            self.json_handler.setFormatter(JsonStreamingFormatter())
            self._logger.addHandler(self.json_handler)

        # Error handler (lazy: added on first ERROR/FATAL)
        self.error_handler = None

        # Shutdown at exit
        atexit.register(self.shutdown)
        self._logger_initialized = True

    def get_logger(self):
        """
        Return the internal logger instance.
        """
        return self.logger

    def _ensure_error_file_handler(self):
        """
        Ensure the error file handler is added if not already.
        """
        if not self.error_handler:
            self.error_handler = logging.FileHandler(self.error_file)
            self.error_handler.setLevel(logging.ERROR)
            self.error_handler.setFormatter(
                AlignedFormatter("%(asctime)s [ %(levelname)s ]  %(message)s")
            )
            self._logger.addHandler(self.error_handler)

    def _write_json_record(self, record):
        """
        Ensure the main log file exists (touch if needed).
        """
        if self.json_handler:
            self.json_handler.handle(record)

    def _ensure_log_file_exists(self):
        """
        Ensure the main log file exists (touch if needed).
        """
        self.log_file.touch(exist_ok=True)

    def _close_json_file(self):
        """
        Close JSON file handler if open.
        """
        if self.json_handler and not self.json_handler.stream.closed:
            self.json_handler.close()

    def shutdown(self):
        """Shutdown logger: flush and close all handlers."""
        for handler in self._logger.handlers[:]:
            try:
                if hasattr(handler.stream, "closed") and not handler.stream.closed:
                    handler.flush()
                    handler.close()
            except (AttributeError, ValueError):
                pass  # Skip if no stream or already closed
            self._logger.removeHandler(handler)

    # ----------------------
    # Convenience methods
    # ----------------------

    def debug(self, msg):
        """Log a message at DEBUG level."""
        self._logger.debug(msg)
        self._write_json_record(
            self._logger.makeRecord(
                LOGGER_NAME, logging.DEBUG, "", 0, msg, args=None, exc_info=None
            )
        )
        self._ensure_log_file_exists()

    def info(self, msg):
        """Log a message at INFO level."""
        self._logger.info(msg)
        self._write_json_record(
            self._logger.makeRecord(
                LOGGER_NAME, logging.INFO, "", 0, msg, args=None, exc_info=None
            )
        )
        self._ensure_log_file_exists()

    def warning(self, msg):
        """Log a message at WARNING level."""
        self._logger.warning(msg)
        self._write_json_record(
            self._logger.makeRecord(
                LOGGER_NAME, logging.WARNING, "", 0, msg, args=None, exc_info=None
            )
        )
        self._ensure_log_file_exists()

    def error(self, msg):
        """Log a message at ERROR level and write to .err file."""
        self._ensure_error_file_handler()
        self._logger.error(msg)
        self._write_json_record(
            self._logger.makeRecord(
                LOGGER_NAME, logging.ERROR, "", 0, msg, args=None, exc_info=None
            )
        )
        self._ensure_log_file_exists()

    def fatal(self, msg):
        """Log a message at FATAL level and write to .err file."""
        self._ensure_error_file_handler()
        self._logger.critical(msg)
        self._write_json_record(
            self._logger.makeRecord(
                LOGGER_NAME, logging.CRITICAL, "", 0, msg, args=None, exc_info=None
            )
        )
        self._ensure_log_file_exists()

    def log(self, level, msg):
        """
        Log a message at the given severity level.

        Args:
            level (str): Logging level ('DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL').
            msg (str): Message to log.
        """
        level = level.upper()
        if level == "FATAL":
            self.fatal(msg)
        elif level == "ERROR":
            self.error(msg)
        elif hasattr(self._logger, level.lower()):
            getattr(self._logger, level.lower())(msg)
            self._write_json_record(
                self._logger.makeRecord(
                    LOGGER_NAME,
                    getattr(logging, level),
                    "",
                    0,
                    msg,
                    args=None,
                    exc_info=None,
                )
            )
        else:
            self.info(msg)
