# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
External secrets providers.

Only env and file providers are implemented now. The provider registry is intentionally
small and explicit so new providers can be added without changing the execution engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any, Dict, Mapping


class SecretProviderError(ValueError):
    """Raised when a secret cannot be resolved."""


class SecretProvider(ABC):
    """Base interface for all secret providers."""

    name: str

    @abstractmethod
    def resolve(self, definition: Mapping[str, Any]) -> str:
        """Resolve one secret definition into a string value."""


class EnvSecretProvider(SecretProvider):
    """Resolve secrets from environment variables."""

    name = "env"

    def resolve(self, definition: Mapping[str, Any]) -> str:
        env_name = definition.get("name") or definition.get("var")
        if not env_name:
            raise SecretProviderError("env secret requires 'name' or 'var'")
        if env_name not in os.environ:
            raise SecretProviderError(f"environment variable not set: {env_name}")
        return os.environ[env_name]


class FileSecretProvider(SecretProvider):
    """Resolve secrets from local files."""

    name = "file"

    def resolve(self, definition: Mapping[str, Any]) -> str:
        raw_path = definition.get("path")
        if not raw_path:
            raise SecretProviderError("file secret requires 'path'")
        path = _resolve_relative_path(str(raw_path), definition.get("_base_dir"))
        if not path.exists():
            raise SecretProviderError(f"secret file not found: {path}")
        value = path.read_text(encoding="utf-8")
        if definition.get("strip", True):
            value = value.strip()
        return value


class CommandSecretProvider(SecretProvider):
    """Resolve secrets by executing an operator-defined local command."""

    name = "command"

    def resolve(self, definition: Mapping[str, Any]) -> str:
        if "command" not in definition:
            raise SecretProviderError("command secret requires 'command'")
        shell = _coerce_bool(definition.get("shell"), default=False)
        command = _coerce_command(definition["command"], shell=shell)
        cwd = definition.get("cwd")
        base_dir = definition.get("_base_dir")
        cwd_path = _resolve_relative_path(str(cwd), base_dir) if cwd else base_dir
        timeout = _coerce_timeout(definition.get("timeout"), default=10)
        env = _build_command_env(definition.get("env"))
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd_path) if cwd_path else None,
                env=env,
                shell=shell,
                check=False,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise SecretProviderError(
                f"command secret timed out after {timeout}s"
            ) from exc
        except OSError as exc:
            raise SecretProviderError(f"command secret failed to start: {exc}") from exc
        if completed.returncode != 0:
            raise SecretProviderError(
                f"command secret failed with exit code {completed.returncode}"
            )
        value = completed.stdout
        if definition.get("strip", True):
            value = value.strip()
        return value


def _resolve_relative_path(path: str, base_dir: Any = None) -> Path:
    resolved = Path(path).expanduser()
    if not resolved.is_absolute() and base_dir:
        resolved = Path(str(base_dir)).expanduser().resolve() / resolved
    return resolved.resolve()


def _coerce_bool(value: Any, *, default: bool) -> bool:
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
    raise SecretProviderError(f"invalid boolean secret option value: {value!r}")


def _coerce_timeout(value: Any, *, default: int) -> int:
    if value is None:
        return default
    parsed = int(value)
    if parsed <= 0:
        raise SecretProviderError("secret command timeout must be a positive integer")
    return parsed


def _coerce_command(command: Any, *, shell: bool) -> Any:
    if isinstance(command, list):
        if shell:
            raise SecretProviderError("command secret cannot use a list with shell: true")
        if not command or not all(isinstance(item, str) for item in command):
            raise SecretProviderError("command secret list command must contain strings")
        return command
    if isinstance(command, str):
        if not command.strip():
            raise SecretProviderError("command secret command cannot be empty")
        return command if shell else shlex.split(command)
    raise SecretProviderError("command secret command must be a string or list")


def _build_command_env(extra_env: Any) -> Dict[str, str] | None:
    if extra_env is None:
        return None
    if not isinstance(extra_env, Mapping):
        raise SecretProviderError("command secret env must be a mapping")
    env = os.environ.copy()
    env.update({str(key): str(value) for key, value in extra_env.items()})
    return env


class SecretManager:
    """Resolve a secrets YAML file through registered providers."""

    def __init__(self, providers: list[SecretProvider] | None = None):
        providers = providers or [EnvSecretProvider(), FileSecretProvider(), CommandSecretProvider()]
        self._providers = {provider.name: provider for provider in providers}

    def register_provider(self, provider: SecretProvider) -> None:
        """Register or replace a provider."""
        self._providers[provider.name] = provider

    def resolve_all(self, document: Mapping[str, Any] | None, *, base_dir: Path | None = None) -> Dict[str, str]:
        """Resolve all secrets from a secrets document."""
        if not document:
            return {}

        raw_secrets = document.get("secrets", document)
        if not isinstance(raw_secrets, Mapping):
            raise SecretProviderError("secrets root must be a mapping")

        resolved: Dict[str, str] = {}
        for key, definition in raw_secrets.items():
            resolved[str(key)] = self._resolve_one(key, definition, base_dir=base_dir)
        return resolved

    def _resolve_one(self, key: Any, definition: Any, *, base_dir: Path | None = None) -> str:
        if isinstance(definition, str):
            return definition
        if not isinstance(definition, Mapping):
            raise SecretProviderError(f"secret '{key}' must be a string or mapping")

        normalized = self._normalize_definition(definition)
        if base_dir is not None:
            normalized.setdefault("_base_dir", base_dir)
        provider_name = normalized.get("provider")
        if not provider_name:
            raise SecretProviderError(f"secret '{key}' requires provider")
        provider = self._providers.get(str(provider_name))
        if not provider:
            raise SecretProviderError(f"unknown secret provider: {provider_name}")
        return provider.resolve(normalized)

    @staticmethod
    def _normalize_definition(definition: Mapping[str, Any]) -> Dict[str, Any]:
        # Shorthand: {env: SSH_PASSWORD} or {file: /path/value}
        if "env" in definition and "provider" not in definition:
            return {"provider": "env", "name": definition["env"]}
        if "file" in definition and "provider" not in definition:
            return {"provider": "file", "path": definition["file"]}
        if "command" in definition and "provider" not in definition:
            return {"provider": "command", "command": definition["command"]}
        return dict(definition)
