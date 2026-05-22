"""
External secrets providers.

Only env and file providers are implemented now. The provider registry is intentionally
small and explicit so new providers can be added without changing the execution engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from pathlib import Path
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
        path = Path(str(raw_path)).expanduser()
        if not path.exists():
            raise SecretProviderError(f"secret file not found: {path}")
        value = path.read_text(encoding="utf-8")
        if definition.get("strip", True):
            value = value.strip()
        return value


class SecretManager:
    """Resolve a secrets YAML file through registered providers."""

    def __init__(self, providers: list[SecretProvider] | None = None):
        providers = providers or [EnvSecretProvider(), FileSecretProvider()]
        self._providers = {provider.name: provider for provider in providers}

    def register_provider(self, provider: SecretProvider) -> None:
        """Register or replace a provider."""
        self._providers[provider.name] = provider

    def resolve_all(self, document: Mapping[str, Any] | None) -> Dict[str, str]:
        """Resolve all secrets from a secrets document."""
        if not document:
            return {}

        raw_secrets = document.get("secrets", document)
        if not isinstance(raw_secrets, Mapping):
            raise SecretProviderError("secrets root must be a mapping")

        resolved: Dict[str, str] = {}
        for key, definition in raw_secrets.items():
            resolved[str(key)] = self._resolve_one(key, definition)
        return resolved

    def _resolve_one(self, key: Any, definition: Any) -> str:
        if isinstance(definition, str):
            return definition
        if not isinstance(definition, Mapping):
            raise SecretProviderError(f"secret '{key}' must be a string or mapping")

        normalized = self._normalize_definition(definition)
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
        return dict(definition)
