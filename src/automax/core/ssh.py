# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
SSH connection management.

The engine opens one SSH connection per step and target, then executes all substeps for
that step through the same connection.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import socket
import tempfile
from typing import Iterator

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
            # Do not silently trust unknown hosts. Operators can provide a known_hosts
            # file or set missing_host_key_policy=auto_add explicitly for lab usage.
            policy = str(target.ssh.get("missing_host_key_policy", "reject"))
            if policy == "auto_add":
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            elif policy == "warning":
                client.set_missing_host_key_policy(paramiko.WarningPolicy())
            else:
                client.set_missing_host_key_policy(paramiko.RejectPolicy())

            known_hosts = target.ssh.get("known_hosts")
            if known_hosts:
                client.load_host_keys(str(Path(known_hosts).expanduser()))
            else:
                try:
                    client.load_system_host_keys()
                except Exception:
                    pass

            key_filename = target.key_file
            if target.key_content:
                temp_key = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
                temp_key.write(target.key_content)
                temp_key.flush()
                temp_key.close()
                key_filename = temp_key.name

            client.connect(
                hostname=target.host,
                port=target.port,
                username=target.user,
                password=target.password,
                key_filename=key_filename,
                timeout=int(target.ssh.get("connect_timeout", self.connect_timeout)),
                banner_timeout=int(target.ssh.get("banner_timeout", self.connect_timeout)),
                auth_timeout=int(target.ssh.get("auth_timeout", self.connect_timeout)),
                look_for_keys=bool(target.ssh.get("look_for_keys", True)),
                allow_agent=bool(target.ssh.get("allow_agent", True)),
            )
            yield client
        except (socket.error, Exception) as exc:
            raise SshError(f"SSH connection failed for {target.name}: {exc}") from exc
        finally:
            if client is not None:
                client.close()
            if temp_key is not None:
                Path(temp_key.name).unlink(missing_ok=True)
