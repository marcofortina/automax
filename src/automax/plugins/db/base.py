# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Shared database plugin helpers.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Sequence

from automax.core.models import PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError


class DatabaseQueryPlugin(BasePlugin):
    """Base class for controller-side transactional database query plugins."""

    required_params: tuple[str, ...] = ()
    optional_params = (
        "connection",
        "query",
        "statements",
        "query_params",
        "output",
        "fetch",
        "commit",
    )
    opens_remote_session = False

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not params.get("query") and not params.get("statements"):
            raise PluginValidationError(f"{self.name} requires query or statements")
        if params.get("query") and params.get("statements"):
            raise PluginValidationError(f"{self.name} accepts query or statements, not both")
        output = str(params.get("output", "rows"))
        if output not in {"rows", "scalar", "json", "none"}:
            raise PluginValidationError("output must be rows, scalar, json or none")
        fetch = str(params.get("fetch", "all"))
        if fetch not in {"all", "one", "none"}:
            raise PluginValidationError("fetch must be all, one or none")

    def _statements(self, params: Dict[str, Any]) -> list[str]:
        if params.get("query"):
            return [str(params["query"])]
        statements = params.get("statements") or []
        if isinstance(statements, str):
            return [statements]
        if not isinstance(statements, list):
            raise PluginValidationError("statements must be a string or list")
        values = [str(item) for item in statements if str(item).strip()]
        if not values:
            raise PluginValidationError("statements must not be empty")
        return values

    def _query_params(self, params: Dict[str, Any]) -> Any:
        return params.get("query_params", ())

    def _format_result(
        self,
        *,
        rows: list[dict[str, Any]],
        rowcount: int,
        output: str,
        statements: Sequence[str],
    ) -> PluginResult:
        scalar = None
        if rows:
            first_row = rows[0]
            scalar = next(iter(first_row.values())) if first_row else None
        data = {
            "rows": rows,
            "rowcount": rowcount,
            "scalar": scalar,
            "statements": len(statements),
            "output": output,
        }
        if output == "none":
            stdout = ""
        elif output == "scalar":
            stdout = "" if scalar is None else str(scalar)
        else:
            stdout = json.dumps(rows if output in {"rows", "json"} else data, default=str)
        return PluginResult.success(changed=rowcount > 0, stdout=stdout, data=data)


def rows_from_cursor_description(description: Iterable[Any], rows: Iterable[Iterable[Any]]) -> List[dict[str, Any]]:
    """Convert DB-API cursor rows to a list of dictionaries."""
    columns = [item[0] for item in description or []]
    return [dict(zip(columns, row)) for row in rows]
