# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation exceptions shared by plugin helpers."""

from __future__ import annotations


class PluginValidationError(ValueError):
    """Raised when plugin parameters are invalid."""
