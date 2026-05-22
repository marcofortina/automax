"""
YAML loading helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class YamlLoadError(ValueError):
    """Raised when a YAML file cannot be loaded as a mapping."""


def load_yaml_file(path: str | Path, *, required: bool = True) -> Dict[str, Any]:
    """Load a YAML file and return a dictionary."""
    yaml_path = Path(path).expanduser().resolve()
    if not yaml_path.exists():
        if required:
            raise YamlLoadError(f"YAML file not found: {yaml_path}")
        return {}

    with yaml_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise YamlLoadError(f"YAML root must be a mapping: {yaml_path}")
    return data
