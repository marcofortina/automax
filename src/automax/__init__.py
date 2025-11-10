"""
Automax - Modular YAML-driven automation framework.

Exposes the public API for programmatic usage.
"""

__version__ = "0.1.1"
__author__ = "Marco Fortina"

from .cli import cli_main
from .main import run_automax

__all__ = [
    "__version__",
    "run_automax",
    "cli_main",
]
