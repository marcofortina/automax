# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Markdown generation for plugin reference documentation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def render_plugin_reference(plugins: Iterable[dict[str, Any]]) -> str:
    """Render canonical plugin metadata into deterministic Markdown."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for plugin in plugins:
        grouped[str(plugin.get("category") or "other")].append(plugin)

    lines = [
        "<!--",
        "Copyright (C) 2026 Marco Fortina",
        "SPDX-License-Identifier: AGPL-3.0-or-later",
        "-->",
        "",
        "# Generated plugin reference",
        "",
        "This file is generated from the installed plugin metadata.",
        "Do not edit plugin parameter lists here by hand; update plugin metadata and regenerate.",
        "",
        "```bash",
        "automax docs generate-plugins --output docs/plugins/generated.md",
        "```",
        "",
    ]

    for category in sorted(grouped):
        lines.extend([f"## {category}", ""])
        for plugin in sorted(grouped[category], key=lambda item: str(item["name"])):
            lines.extend(_render_plugin(plugin))
    return "\n".join(lines).rstrip() + "\n"


def _render_plugin(plugin: dict[str, Any]) -> list[str]:
    lines = [f"### `{plugin['name']}`", ""]
    description = str(plugin.get("description") or "No description provided.")
    lines.extend([description, ""])
    lines.extend(
        [
            f"- Remote session: `{str(plugin.get('opens_remote_session', False)).lower()}`",
            f"- Dry-run support: `{str(plugin.get('supports_dry_run', False)).lower()}`",
            f"- Check mode support: `{str(plugin.get('supports_check_mode', False)).lower()}`",
            "",
        ]
    )

    parameters = plugin.get("parameters") or []
    if parameters:
        lines.extend(["| Parameter | Required | Type | Default | Description |", "|---|---:|---|---|---|"])
        for parameter in parameters:
            default = parameter.get("default")
            default_text = "" if default is None else f"`{default}`"
            description = str(parameter.get("description") or "-").replace("|", "\\|")
            lines.append(
                "| `{name}` | {required} | `{type}` | {default} | {description} |".format(
                    name=parameter["name"],
                    required="yes" if parameter.get("required") else "no",
                    type=parameter.get("type", "any"),
                    default=default_text,
                    description=description,
                )
            )
        lines.append("")
    else:
        lines.extend(["Parameters: none.", ""])

    result_fields = plugin.get("result_fields") or {}
    if result_fields:
        lines.extend(["Result fields:", ""])
        for key, value in result_fields.items():
            lines.append(f"- `{key}`: {value}")
        lines.append("")

    examples = plugin.get("examples") or []
    for example in examples:
        lines.extend(["Example:", "", "```yaml", str(example), "```", ""])

    return lines
