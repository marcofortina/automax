"""
Controlled Jinja2 rendering for job data structures.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from jinja2 import StrictUndefined
from jinja2 import Template
from jinja2 import UndefinedError


class TemplateRenderError(ValueError):
    """Raised when a template cannot be rendered."""


def render_value(value: Any, context: Dict[str, Any]) -> Any:
    """Render strings recursively while preserving non-string values."""
    if isinstance(value, str):
        try:
            return Template(value, undefined=StrictUndefined).render(**context)
        except UndefinedError as exc:
            raise TemplateRenderError(str(exc)) from exc
    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render_value(item, context) for key, item in value.items()}
    return value


def render_mapping(data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Render a mapping without mutating the original object."""
    return render_value(deepcopy(data), context)
