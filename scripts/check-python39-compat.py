# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Guard runtime compatibility with Python 3.9.

Automax supports Python 3.9+. ``from __future__ import annotations`` keeps modern
annotation syntax safe, but PEP 604 unions such as ``int | float`` must not be
used as runtime values in calls like ``isinstance`` or ``issubclass`` on Python
3.9. This checker catches the most likely regression before CI has to fail on a
3.9 runner.
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys

CHECKED_ROOTS = (Path("src"), Path("tests"), Path("scripts"))


class Python39CompatibilityVisitor(ast.NodeVisitor):
    """Detect syntax patterns that parse but fail at runtime on Python 3.9."""

    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_builtin_call(node, {"isinstance", "issubclass"}):
            if len(node.args) >= 2 and self._contains_runtime_union(node.args[1]):
                self.errors.append(
                    f"{self.path}:{node.lineno}:{node.col_offset}: "
                    "use a tuple for isinstance/issubclass checks on Python 3.9"
                )
        self.generic_visit(node)

    @staticmethod
    def _is_builtin_call(node: ast.Call, names: set[str]) -> bool:
        return isinstance(node.func, ast.Name) and node.func.id in names

    def _contains_runtime_union(self, node: ast.AST) -> bool:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return True
        return any(self._contains_runtime_union(child) for child in ast.iter_child_nodes(node))


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in CHECKED_ROOTS:
        if root.exists():
            files.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return sorted(files)


def main() -> int:
    errors: list[str] = []
    for path in _iter_python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path}:{exc.lineno}:{exc.offset}: {exc.msg}")
            continue
        visitor = Python39CompatibilityVisitor(path)
        visitor.visit(tree)
        errors.extend(visitor.errors)

    if errors:
        print("Python 3.9 compatibility check failed:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("Python 3.9 compatibility check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
