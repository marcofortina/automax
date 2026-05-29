# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Controlled Jinja2 rendering for job data structures.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from jinja2 import Environment
from jinja2 import StrictUndefined
from jinja2 import UndefinedError
from jinja2 import select_autoescape
from jinja2.nativetypes import NativeEnvironment


class TemplateRenderError(ValueError):
    """Raised when a template cannot be rendered."""


_NATIVE_TEMPLATE_ENV = NativeEnvironment(undefined=StrictUndefined)


_TEXT_TEMPLATE_ENV = Environment(
    autoescape=select_autoescape(
        enabled_extensions=("html", "htm", "xml"),
        default_for_string=False,
        default=False,
    ),
    undefined=StrictUndefined,
)


def render_template_string(template_source: str, context: Dict[str, Any]) -> str:
    """Render a trusted text/config template with strict undefined variables."""
    try:
        return _TEXT_TEMPLATE_ENV.from_string(template_source).render(**context)
    except UndefinedError as exc:
        raise TemplateRenderError(str(exc)) from exc


def evaluate_value(value: Any, context: Dict[str, Any]) -> Any:
    """Evaluate one trusted Jinja expression while preserving native Python types."""
    if not isinstance(value, str):
        return render_value(value, context)
    try:
        return _NATIVE_TEMPLATE_ENV.from_string(value).render(**context)
    except UndefinedError as exc:
        raise TemplateRenderError(str(exc)) from exc


def render_value(value: Any, context: Dict[str, Any]) -> Any:
    """Render strings recursively while preserving non-string values."""
    if isinstance(value, str):
        return render_template_string(value, context)
    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render_value(item, context) for key, item in value.items()}
    return value


def render_mapping(data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Render a mapping without mutating the original object."""
    return render_value(deepcopy(data), context)
