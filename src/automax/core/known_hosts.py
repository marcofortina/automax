# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Safe SSH known_hosts scanning helpers."""

from __future__ import annotations

import base64
import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from automax.core.models import Target


class KnownHostsError(ValueError):
    """Raised when host key scanning cannot produce usable output."""


@dataclass(frozen=True)
class KnownHostEntry:
    """One scanned OpenSSH known_hosts line plus fingerprint metadata."""

    target_name: str
    host: str
    port: int
    key_type: str
    fingerprint: str
    line: str


def scan_known_hosts(
    targets: Iterable[Target], *, timeout: int = 5, key_types: Iterable[str] = ()
) -> list[KnownHostEntry]:
    """Run ssh-keyscan for targets and return parsed key lines.

    This helper only collects public host keys. It does not mark them trusted;
    operators must verify fingerprints before using the resulting file.
    """
    entries: list[KnownHostEntry] = []
    for target in targets:
        entries.extend(_scan_target(target, timeout=timeout, key_types=key_types))
    return entries


def write_known_hosts(entries: Iterable[KnownHostEntry], path: str | Path, *, append: bool = False) -> Path:
    """Write scanned known_hosts lines to an explicit operator-provided path."""
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with output.open(mode, encoding="utf-8") as handle:
        for entry in entries:
            handle.write(entry.line.rstrip("\n") + "\n")
    return output


def _scan_target(target: Target, *, timeout: int, key_types: Iterable[str]) -> list[KnownHostEntry]:
    command = ["ssh-keyscan", "-T", str(timeout), "-p", str(target.port)]
    key_type_list = [str(item) for item in key_types if str(item).strip()]
    if key_type_list:
        command.extend(["-t", ",".join(key_type_list)])
    command.append(target.host)
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout + 2,
        )
    except FileNotFoundError as exc:
        raise KnownHostsError("ssh-keyscan not found in PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise KnownHostsError(f"ssh-keyscan timed out for {target.name} ({target.host})") from exc
    if completed.returncode != 0 and not completed.stdout.strip():
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise KnownHostsError(f"ssh-keyscan failed for {target.name} ({target.host}): {detail}")

    entries = []
    for line in completed.stdout.splitlines():
        parsed = _parse_known_host_line(line, target)
        if parsed is not None:
            entries.append(parsed)
    if not entries:
        raise KnownHostsError(f"ssh-keyscan returned no host keys for {target.name} ({target.host})")
    return entries


def _parse_known_host_line(line: str, target: Target) -> KnownHostEntry | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parts = stripped.split()
    if len(parts) < 3:
        return None
    key_type = parts[1]
    key_blob = parts[2]
    return KnownHostEntry(
        target_name=target.name,
        host=target.host,
        port=target.port,
        key_type=key_type,
        fingerprint=_fingerprint(key_blob),
        line=stripped,
    )


def _fingerprint(key_blob: str) -> str:
    try:
        raw = base64.b64decode(key_blob.encode("ascii"), validate=True)
    except Exception as exc:
        raise KnownHostsError("ssh-keyscan returned an invalid base64 host key") from exc
    digest = base64.b64encode(hashlib.sha256(raw).digest()).decode("ascii").rstrip("=")
    return f"SHA256:{digest}"
