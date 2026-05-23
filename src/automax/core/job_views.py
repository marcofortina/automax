# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Human-oriented views for planned Automax jobs."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, Iterable, List


def build_job_view(job: Dict[str, Any], plan: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a stable, serializable view from a resolved execution plan."""
    tasks: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    targets = OrderedDict()
    nodes: List[Dict[str, Any]] = []
    for item in plan:
        task = item["task"]
        step = item["step"]
        substep = item["substep"]
        target = item["target"]
        targets[target.name] = target.host
        task_id = str(task["id"])
        step_id = str(step["id"])
        substep_id = str(substep["id"])
        task_entry = tasks.setdefault(
            task_id,
            {
                "id": task_id,
                "name": task.get("name") or task_id,
                "description": task.get("description", ""),
                "targets": OrderedDict(),
                "steps": OrderedDict(),
            },
        )
        task_entry["targets"][target.name] = target.host
        step_entry = task_entry["steps"].setdefault(
            step_id,
            {
                "id": step_id,
                "name": step.get("name") or step_id,
                "description": step.get("description", ""),
                "targets": OrderedDict(),
                "opens_ssh": False,
                "substeps": OrderedDict(),
            },
        )
        step_entry["targets"][target.name] = target.host
        plugin_name = str(substep.get("use") or substep.get("plugin"))
        if plugin_name != "local.command":
            step_entry["opens_ssh"] = True
        substep_entry = step_entry["substeps"].setdefault(
            substep_id,
            {
                "id": substep_id,
                "name": substep.get("name") or substep_id,
                "description": substep.get("description", ""),
                "plugin": plugin_name,
                "node_id": item["node_id"],
                "tags": list(item.get("tags") or ()),
                "targets": OrderedDict(),
                "checkpoint": item["node_id"],
            },
        )
        substep_entry["targets"][target.name] = target.host
        nodes.append(
            {
                "target": target.name,
                "target_host": target.host,
                "node_id": item["node_id"],
                "task_id": task_id,
                "step_id": step_id,
                "substep_id": substep_id,
                "plugin": plugin_name,
                "tags": list(item.get("tags") or ()),
            }
        )
    return {
        "job": {
            "name": (job.get("metadata") or {}).get("name") or "unnamed-job",
            "description": (job.get("metadata") or {}).get("description", ""),
        },
        "targets": [{"name": name, "host": host} for name, host in targets.items()],
        "tasks": [_normalize_task(task) for task in tasks.values()],
        "nodes": nodes,
        "resume_points": [node["node_id"] for node in nodes],
    }


def render_explain_text(view: Dict[str, Any]) -> str:
    """Render an operator-focused explanation of a planned job."""
    lines = [f"Job: {view['job']['name']}"]
    if view["job"].get("description"):
        lines.append(f"Description: {view['job']['description']}")
    lines.append(f"Targets: {', '.join(target['name'] for target in view['targets']) or '-'}")
    lines.append("")
    for task in view["tasks"]:
        lines.append(f"Task {task['id']} -> targets: {_target_names(task['targets'])}")
        if task.get("description"):
            lines.append(f"  {task['description']}")
        for step in task["steps"]:
            ssh_text = "opens a new SSH connection per target" if step["opens_ssh"] else "controller/local execution"
            lines.append(f"  Step {step['id']} -> {ssh_text}; targets: {_target_names(step['targets'])}")
            if step.get("description"):
                lines.append(f"    {step['description']}")
            for substep in step["substeps"]:
                tags = f" tags={','.join(substep['tags'])}" if substep.get("tags") else ""
                lines.append(
                    f"    Substep {substep['id']} -> {substep['plugin']}; "
                    f"targets: {_target_names(substep['targets'])}; checkpoint: {substep['checkpoint']}{tags}"
                )
    lines.append("")
    lines.append("Resume points:")
    for point in view["resume_points"]:
        lines.append(f"  {point}")
    return "\n".join(lines) + "\n"


def _normalize_task(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **{key: value for key, value in task.items() if key not in {"targets", "steps"}},
        "targets": [{"name": name, "host": host} for name, host in task["targets"].items()],
        "steps": [_normalize_step(step) for step in task["steps"].values()],
    }


def _normalize_step(step: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **{key: value for key, value in step.items() if key not in {"targets", "substeps"}},
        "targets": [{"name": name, "host": host} for name, host in step["targets"].items()],
        "substeps": [_normalize_substep(substep) for substep in step["substeps"].values()],
    }


def _normalize_substep(substep: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **{key: value for key, value in substep.items() if key != "targets"},
        "targets": [{"name": name, "host": host} for name, host in substep["targets"].items()],
    }


def _target_names(targets: Iterable[Dict[str, str]]) -> str:
    return ", ".join(target["name"] for target in targets) or "-"


def render_mermaid(view: Dict[str, Any]) -> str:
    """Render a Mermaid flowchart for a planned job."""
    lines = ["flowchart TD"]
    job_id = _graph_id("job")
    lines.append(f"  {job_id}[{_mermaid_label(view['job']['name'])}]")
    for task in view["tasks"]:
        task_id = _graph_id(f"task_{task['id']}")
        lines.append(f"  {job_id} --> {task_id}[Task: {_mermaid_label(task['id'])}]")
        for step in task["steps"]:
            step_id = _graph_id(f"step_{task['id']}_{step['id']}")
            lines.append(f"  {task_id} --> {step_id}[Step: {_mermaid_label(step['id'])}]")
            for substep in step["substeps"]:
                substep_id = _graph_id(f"substep_{task['id']}_{step['id']}_{substep['id']}")
                label = f"{_mermaid_label(substep['id'])}<br/>{_mermaid_label(substep['plugin'])}"
                lines.append(f"  {step_id} --> {substep_id}[{label}]")
    return "\n".join(lines) + "\n"


def render_dot(view: Dict[str, Any]) -> str:
    """Render a Graphviz DOT graph for a planned job."""
    import json
    lines = ["digraph automax_job {", "  rankdir=TB;", "  node [shape=box, style=rounded];"]
    job_id = _graph_id("job")
    lines.append(f"  {job_id} [label={json.dumps(view['job']['name'])}];")
    for task in view["tasks"]:
        task_id = _graph_id(f"task_{task['id']}")
        lines.append(f"  {task_id} [label={json.dumps('Task: ' + task['id'])}];")
        lines.append(f"  {job_id} -> {task_id};")
        for step in task["steps"]:
            step_id = _graph_id(f"step_{task['id']}_{step['id']}")
            lines.append(f"  {step_id} [label={json.dumps('Step: ' + step['id'])}];")
            lines.append(f"  {task_id} -> {step_id};")
            for substep in step["substeps"]:
                substep_id = _graph_id(f"substep_{task['id']}_{step['id']}_{substep['id']}")
                label = f"{substep['id']}\n{substep['plugin']}"
                lines.append(f"  {substep_id} [label={json.dumps(label)}];")
                lines.append(f"  {step_id} -> {substep_id};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_svg(view: Dict[str, Any]) -> str:
    """Render a dependency-free SVG graph."""
    from html import escape
    rows: List[tuple[int, str]] = [(0, view["job"]["name"])]
    for task in view["tasks"]:
        rows.append((1, f"Task: {task['id']}"))
        for step in task["steps"]:
            rows.append((2, f"Step: {step['id']}"))
            for substep in step["substeps"]:
                rows.append((3, f"{substep['id']} ({substep['plugin']})"))
    width = 960
    row_h = 58
    height = max(120, 40 + row_h * len(rows))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;font-size:14px}.box{fill:#eef7f7;stroke:#278080;stroke-width:1.5}.line{stroke:#777;stroke-width:1.2}</style>',
    ]
    prev_center: tuple[int, int] | None = None
    for index, (level, label) in enumerate(rows):
        x = 30 + level * 170
        y = 25 + index * row_h
        w = 250
        h = 36
        center = (x + w // 2, y + h // 2)
        if prev_center is not None:
            parts.append(f'<line class="line" x1="{prev_center[0]}" y1="{prev_center[1]}" x2="{center[0]}" y2="{center[1]}"/>')
        parts.append(f'<rect class="box" x="{x}" y="{y}" rx="8" ry="8" width="{w}" height="{h}"/>')
        parts.append(f'<text x="{x + 12}" y="{y + 23}">{escape(label[:42])}</text>')
        prev_center = center
    parts.append("</svg>\n")
    return "\n".join(parts)


def _graph_id(value: str) -> str:
    import re
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    return cleaned


def _mermaid_label(value: str) -> str:
    return str(value).replace('"', "'").replace("[", "(").replace("]", ")")
