# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Typed runtime models for the new Automax execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class NodeStatus(str, Enum):
    """Persisted execution status for job nodes."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Target:
    """Resolved server target from inventory."""

    name: str
    host: str
    port: int = 22
    user: Optional[str] = None
    password: Optional[str] = None
    key_file: Optional[str] = None
    key_content: Optional[str] = None
    groups: tuple[str, ...] = ()
    vars: Dict[str, Any] = field(default_factory=dict)
    ssh: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginResult:
    """Normalized result returned by every plugin."""

    ok: bool
    changed: bool = False
    skipped: bool = False
    warning: bool = False
    rc: int = 0
    stdout: str = ""
    stderr: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        *,
        changed: bool = False,
        stdout: str = "",
        stderr: str = "",
        rc: int = 0,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> "PluginResult":
        return cls(
            ok=True,
            changed=changed,
            rc=rc,
            stdout=stdout,
            stderr=stderr,
            message=message,
            data=data or {},
        )

    @classmethod
    def failure(
        cls,
        *,
        rc: int = 1,
        stdout: str = "",
        stderr: str = "",
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> "PluginResult":
        return cls(
            ok=False,
            changed=False,
            rc=rc,
            stdout=stdout,
            stderr=stderr,
            message=message,
            data=data or {},
        )

    @classmethod
    def skipped_result(cls, message: str = "") -> "PluginResult":
        return cls(ok=True, skipped=True, message=message)


    @classmethod
    def warning_result(
        cls,
        *,
        changed: bool = False,
        rc: int = 0,
        stdout: str = "",
        stderr: str = "",
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> "PluginResult":
        return cls(
            ok=True,
            changed=changed,
            warning=True,
            rc=rc,
            stdout=stdout,
            stderr=stderr,
            message=message,
            data=data or {},
        )


@dataclass
class ExecutionContext:
    """Runtime context passed to plugins."""

    run_id: str
    dry_run: bool
    job: Dict[str, Any]
    task: Dict[str, Any]
    step: Dict[str, Any]
    substep: Dict[str, Any]
    target: Target
    vars: Dict[str, Any]
    outputs: Dict[str, Any]
    secrets: Dict[str, Any]
    ssh_client: Any = None
    logger: Any = None
    command_timeout: int | None = None
    step_state: Dict[str, Any] = field(default_factory=dict)
