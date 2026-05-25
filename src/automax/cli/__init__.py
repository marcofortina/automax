# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
CLI package for Automax.
"""

from __future__ import annotations

from typing import Any

__all__ = ["cli_main"]


def __getattr__(name: str) -> Any:
    """Load the Click entry point lazily.

    Importing ``automax.cli.cli`` from this package initializer makes
    ``python -m automax.cli.cli`` emit a runpy RuntimeWarning because the target
    module is already present in ``sys.modules`` before runpy executes it. Keep
    the public ``automax.cli:cli_main`` entry point while avoiding the eager
    module import.
    """
    if name == "cli_main":
        from automax.cli.cli import cli_main

        return cli_main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
