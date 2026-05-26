# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
CLI package for Automax.
"""

from __future__ import annotations

__all__ = ["cli_main"]


def cli_main() -> None:
    """Run the Click entry point without importing it during package init.

    Importing ``automax.cli.cli`` from this package initializer makes
    ``python -m automax.cli.cli`` emit a runpy RuntimeWarning because the target
    module is already present in ``sys.modules`` before runpy executes it. Keep
    the public ``automax.cli:cli_main`` entry point while avoiding the eager
    module import.
    """
    from automax.cli.cli import cli_main as _cli_main

    _cli_main()
