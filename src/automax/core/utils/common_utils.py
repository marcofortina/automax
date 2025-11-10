"""
Common utility functions for Automax project.

Includes:
- echo: unified message logging
- Custom exceptions for error handling
- Plugin loading for utilities
"""

from automax.core.managers.logger_manager import LoggerManager


def echo(msg, logger: LoggerManager, level="INFO"):
    """
    Log a message via provided LoggerManager and echo to console.

    Args:
        msg (str): Message to log
        logger (LoggerManager): Logger instance
        level (str): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')

    Returns:
        None
    """
    level = level.upper()
    if level == "DEBUG":
        logger.debug(msg)
    elif level == "INFO":
        logger.info(msg)
    elif level == "WARNING":
        logger.warning(msg)
    elif level == "ERROR":
        logger.error(msg)
    else:
        logger.info(msg)
