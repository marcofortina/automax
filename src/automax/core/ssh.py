# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
SSH connection management.

The engine opens one SSH connection per step and target, then executes all substeps for
that step through the same connection.
"""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import socket
import stat
import tempfile
from typing import Any

from automax.core.models import Target


class SshError(RuntimeError):
    """Raised when an SSH connection cannot be opened."""


class SshSessionManager:
    """Open Paramiko SSH clients from resolved targets."""

    def __init__(self, *, connect_timeout: int = 20):
        self.connect_timeout = connect_timeout

    @contextmanager
    def connect(self, target: Target):
        """Open a new SSH client for one step/target scope."""
        client = None
        temp_key = None
        try:
            import paramiko
        except ImportError as exc:
            raise SshError("paramiko is required for remote execution") from exc

        try:
            client = paramiko.SSHClient()
            self._configure_host_key_policy(client, target, paramiko)

            key_filename = self._resolve_key_filename(target)
            if target.key_content:
                temp_key = self._write_temp_private_key(target.key_content)
                key_filename = temp_key.name

            client.connect(
                hostname=target.host,
                port=target.port,
                username=target.user,
                password=target.password,
                key_filename=key_filename,
                timeout=self._coerce_int(
                    target.ssh.get("connect_timeout"), self.connect_timeout
                ),
                banner_timeout=self._coerce_int(
                    target.ssh.get("banner_timeout"), self.connect_timeout
                ),
                auth_timeout=self._coerce_int(
                    target.ssh.get("auth_timeout"), self.connect_timeout
                ),
                look_for_keys=self._coerce_bool(target.ssh.get("look_for_keys"), False),
                allow_agent=self._coerce_bool(target.ssh.get("allow_agent"), False),
            )
            yield client
        except (socket.error, Exception) as exc:
            raise SshError(f"SSH connection failed for {target.name}: {exc}") from exc
        finally:
            if client is not None:
                client.close()
            if temp_key is not None:
                Path(temp_key.name).unlink(missing_ok=True)

    def _configure_host_key_policy(self, client: Any, target: Target, paramiko: Any) -> None:
        policy = str(target.ssh.get("missing_host_key_policy", "reject")).lower()
        if policy != "reject":
            raise SshError(
                "missing_host_key_policy must be 'reject'; configure known_hosts "
                "or system host keys before connecting"
            )
        client.set_missing_host_key_policy(paramiko.RejectPolicy())

        known_hosts = target.ssh.get("known_hosts")
        if known_hosts:
            known_hosts_path = Path(str(known_hosts)).expanduser()
            if not known_hosts_path.is_file():
                raise SshError(f"known_hosts file not found: {known_hosts_path}")
            client.load_host_keys(str(known_hosts_path))
        else:
            client.load_system_host_keys()

    def _resolve_key_filename(self, target: Target) -> str | None:
        key_filename = target.key_file
        if not key_filename:
            return None
        key_path = Path(str(key_filename)).expanduser()
        if not key_path.is_file():
            raise SshError(f"SSH private key file not found: {key_path}")
        if self._coerce_bool(target.ssh.get("strict_key_permissions"), True):
            self._validate_private_key_permissions(key_path)
        return str(key_path)

    @staticmethod
    def _validate_private_key_permissions(path: Path) -> None:
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise SshError(
                f"SSH private key file is accessible by group/others: {path}. "
                "Use chmod 600 or set strict_key_permissions: false for labs."
            )

    @staticmethod
    def _write_temp_private_key(content: str):
        temp_key = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        try:
            temp_key.write(content)
            temp_key.flush()
            temp_key.close()
            os.chmod(temp_key.name, 0o600)
            return temp_key
        except Exception:
            Path(temp_key.name).unlink(missing_ok=True)
            raise

    @staticmethod
    def _coerce_bool(value: Any, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise SshError(f"invalid boolean SSH option value: {value!r}")

    @staticmethod
    def _coerce_int(value: Any, default: int) -> int:
        if value is None:
            return default
        parsed = int(value)
        if parsed <= 0:
            raise SshError("SSH timeout values must be positive integers")
        return parsed
