"""
Custom exceptions for Automax project.
"""


class AutomaxError(Exception):
    """
    Custom exception for Automax errors, distinguishing between ERROR (continuable) and
    FATAL (stops execution).

    Args:
        message (str): Error message
        level (str): 'ERROR' or 'FATAL' (default: 'ERROR')

    """

    def __init__(self, message, level="ERROR"):
        self.message = message
        self.level = level.upper()
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.level}] {self.message}"
