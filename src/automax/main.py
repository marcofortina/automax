# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Public Python API for Automax next engine.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from automax.core.engine import AutomaxEngine


def run_automax(
    *,
    job_path: str,
    inventory_path: str,
    vars_path: str | None = None,
    secrets_path: str | None = None,
    state_dir: str = ".automax/runs",
    dry_run: bool = False,
    plan_only: bool = False,
    from_node: str | None = None,
    limit: Iterable[str] = (),
    exclude: Iterable[str] = (),
    tags: Iterable[str] = (),
    skip_tags: Iterable[str] = (),
    cli_vars: Optional[Dict[str, Any]] = None,
    sudo_password_env: str | None = None,
) -> int:
    """Run Automax from external job/inventory/vars/secrets files."""
    engine = AutomaxEngine()
    return engine.run(
        job_path=job_path,
        inventory_path=inventory_path,
        vars_path=vars_path,
        secrets_path=secrets_path,
        state_dir=state_dir,
        dry_run=dry_run,
        plan_only=plan_only,
        from_node=from_node,
        limit=limit,
        exclude=exclude,
        tags=tags,
        skip_tags=skip_tags,
        cli_vars=cli_vars,
        sudo_password_env=sudo_password_env,
    )
