# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Inventory parsing and target selection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from automax.core.models import Target
from automax.core.templating import render_mapping


class InventoryError(ValueError):
    """Raised when inventory cannot be parsed or resolved."""


def load_inventory_document(path: str | Path, context: Dict[str, Any]) -> Dict[str, Any]:
    """Load a static or dynamic inventory document from an external YAML file."""
    from automax.core.yaml_loader import load_yaml_file

    inventory_path = Path(path).expanduser().resolve()
    document = load_yaml_file(inventory_path)
    return resolve_inventory_document(document, base_dir=inventory_path.parent, context=context)


def resolve_inventory_document(
    document: Mapping[str, Any], *, base_dir: Path, context: Dict[str, Any]
) -> Dict[str, Any]:
    """Resolve static, file, command or HTTP inventory provider definitions."""
    rendered = render_mapping(dict(document or {}), context)
    if "servers" in rendered:
        return rendered

    provider_definition = rendered.get("inventory", rendered)
    if not isinstance(provider_definition, Mapping):
        raise InventoryError("dynamic inventory provider definition must be a mapping")

    provider_name = str(provider_definition.get("provider", "")).strip().lower()
    if not provider_name:
        raise InventoryError("inventory provider definition requires 'provider'")
    if provider_name == "file":
        return _load_file_inventory(provider_definition, base_dir=base_dir, context=context)
    if provider_name == "command":
        return _load_command_inventory(provider_definition, base_dir=base_dir, context=context)
    if provider_name == "http":
        return _load_http_inventory(provider_definition, context=context)
    raise InventoryError(f"unknown inventory provider: {provider_name}")


def _load_file_inventory(
    definition: Mapping[str, Any], *, base_dir: Path, context: Dict[str, Any]
) -> Dict[str, Any]:
    raw_path = definition.get("path")
    if not raw_path:
        raise InventoryError("file inventory provider requires 'path'")
    inventory_path = _resolve_relative_path(str(raw_path), base_dir)
    from automax.core.yaml_loader import load_yaml_file

    return resolve_inventory_document(
        load_yaml_file(inventory_path),
        base_dir=inventory_path.parent,
        context=context,
    )


def _load_command_inventory(
    definition: Mapping[str, Any], *, base_dir: Path, context: Dict[str, Any]
) -> Dict[str, Any]:
    import subprocess

    if "command" not in definition:
        raise InventoryError("command inventory provider requires 'command'")
    shell = _coerce_bool(definition.get("shell"), default=False)
    command = _coerce_command(definition["command"], shell=shell)
    cwd = definition.get("cwd")
    cwd_path = _resolve_relative_path(str(cwd), base_dir) if cwd else base_dir
    env = _build_provider_env(definition.get("env"))
    timeout = _coerce_timeout(definition.get("timeout"), default=30)
    try:
        completed = subprocess.run(
            command if shell else command,
            cwd=str(cwd_path),
            env=env,
            shell=shell,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise InventoryError(f"command inventory provider timed out after {timeout}s") from exc
    except OSError as exc:
        raise InventoryError(f"command inventory provider failed to start: {exc}") from exc
    if completed.returncode != 0:
        raise InventoryError(
            f"command inventory provider failed with exit code {completed.returncode}"
        )
    return _parse_provider_payload(
        completed.stdout,
        provider="command",
        payload_format=str(definition.get("format", "auto")),
        context=context,
    )


def _load_http_inventory(
    definition: Mapping[str, Any], *, context: Dict[str, Any]
) -> Dict[str, Any]:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    url = definition.get("url")
    if not url:
        raise InventoryError("http inventory provider requires 'url'")
    method = str(definition.get("method", "GET")).upper()
    if method != "GET":
        raise InventoryError("http inventory provider currently supports only GET")
    headers = definition.get("headers") or {}
    if not isinstance(headers, Mapping):
        raise InventoryError("http inventory provider 'headers' must be a mapping")
    timeout = _coerce_timeout(definition.get("timeout"), default=30)
    request = Request(str(url), headers={str(k): str(v) for k, v in headers.items()})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - operator-provided URL
            raw_payload = response.read().decode(str(definition.get("encoding", "utf-8")))
    except HTTPError as exc:
        raise InventoryError(f"http inventory provider failed with status {exc.code}") from exc
    except URLError as exc:
        raise InventoryError(f"http inventory provider failed: {exc.reason}") from exc
    return _parse_provider_payload(
        raw_payload,
        provider="http",
        payload_format=str(definition.get("format", "auto")),
        context=context,
    )


def _parse_provider_payload(
    payload: str, *, provider: str, payload_format: str, context: Dict[str, Any]
) -> Dict[str, Any]:
    import json
    import yaml

    normalized_format = payload_format.strip().lower()
    if normalized_format not in {"auto", "yaml", "json"}:
        raise InventoryError("inventory provider format must be one of: auto, yaml, json")
    try:
        if normalized_format == "json":
            parsed = json.loads(payload)
        else:
            parsed = yaml.safe_load(payload)
    except Exception as exc:
        raise InventoryError(f"{provider} inventory provider returned invalid payload") from exc
    if not isinstance(parsed, dict):
        raise InventoryError(f"{provider} inventory provider must return a mapping")
    rendered = render_mapping(parsed, context)
    if "servers" not in rendered:
        raise InventoryError(f"{provider} inventory provider returned no 'servers' mapping")
    return rendered


def _coerce_command(command: Any, *, shell: bool) -> Any:
    import shlex

    if isinstance(command, list):
        if shell:
            raise InventoryError("command inventory provider cannot use a list with shell: true")
        if not command or not all(isinstance(item, str) for item in command):
            raise InventoryError("command inventory provider list command must contain strings")
        return command
    if isinstance(command, str):
        if not command.strip():
            raise InventoryError("command inventory provider command cannot be empty")
        return command if shell else shlex.split(command)
    raise InventoryError("command inventory provider command must be a string or list")


def _build_provider_env(extra_env: Any) -> Dict[str, str] | None:
    import os

    if extra_env is None:
        return None
    if not isinstance(extra_env, Mapping):
        raise InventoryError("inventory provider env must be a mapping")
    env = os.environ.copy()
    env.update({str(key): str(value) for key, value in extra_env.items()})
    return env


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
    raise InventoryError(f"invalid boolean inventory provider option value: {value!r}")


def _coerce_timeout(value: Any, *, default: int) -> int:
    if value is None:
        return default
    parsed = int(value)
    if parsed <= 0:
        raise InventoryError("inventory provider timeout must be a positive integer")
    return parsed


def _resolve_relative_path(path: str, base_dir: Path) -> Path:
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = base_dir / resolved
    return resolved.resolve()


class Inventory:
    """Resolved external inventory."""

    def __init__(self, document: Mapping[str, Any] | None, context: Dict[str, Any]):
        self.document = render_mapping(dict(document or {}), context)
        self.targets = self._parse_servers(self.document)
        self.groups = self._parse_groups(self.document, self.targets)

    def select(
        self,
        selector: Any = None,
        *,
        limit: Sequence[str] | None = None,
        exclude: Sequence[str] | None = None,
    ) -> List[Target]:
        """Select targets by explicit selector plus optional CLI limit/exclude."""
        selected = self._select_from_selector(selector)
        if limit:
            limited = []
            for item in limit:
                limited.extend(self._select_from_selector(item))
            allowed = {target.name for target in limited}
            selected = [target for target in selected if target.name in allowed]
        if exclude:
            excluded = set()
            for item in exclude:
                excluded.update(target.name for target in self._select_from_selector(item))
            selected = [target for target in selected if target.name not in excluded]
        return self._dedupe(selected)

    def _select_from_selector(self, selector: Any) -> List[Target]:
        if selector is None:
            selector = "all"
        if isinstance(selector, str):
            return self._select_one(selector)
        if isinstance(selector, list):
            selected: List[Target] = []
            for item in selector:
                selected.extend(self._select_from_selector(item))
            return self._dedupe(selected)
        raise InventoryError(f"invalid target selector: {selector!r}")

    def _select_one(self, selector: str) -> List[Target]:
        selector = selector.strip()
        if selector in ("all", "*"):
            return list(self.targets.values())
        if selector.startswith("group:"):
            group = selector.split(":", 1)[1]
            return [self.targets[name] for name in self.groups.get(group, [])]
        if selector.startswith("server:"):
            name = selector.split(":", 1)[1]
            return [self._get_target(name)]
        if selector in self.groups:
            return [self.targets[name] for name in self.groups[selector]]
        if selector in self.targets:
            return [self.targets[selector]]
        raise InventoryError(f"unknown target selector: {selector}")

    def _get_target(self, name: str) -> Target:
        try:
            return self.targets[name]
        except KeyError as exc:
            raise InventoryError(f"unknown server: {name}") from exc

    @staticmethod
    def _dedupe(targets: Iterable[Target]) -> List[Target]:
        seen = set()
        result = []
        for target in targets:
            if target.name in seen:
                continue
            seen.add(target.name)
            result.append(target)
        return result

    @staticmethod
    def _parse_servers(document: Mapping[str, Any]) -> Dict[str, Target]:
        raw_servers = document.get("servers", {})
        servers: Dict[str, Target] = {}

        if isinstance(raw_servers, Mapping):
            iterable = raw_servers.items()
        elif isinstance(raw_servers, list):
            iterable = []
            for entry in raw_servers:
                if not isinstance(entry, Mapping) or "name" not in entry:
                    raise InventoryError("server list entries require 'name'")
                iterable.append((entry["name"], entry))
        else:
            raise InventoryError("inventory 'servers' must be a mapping or list")

        for name, data in iterable:
            if not isinstance(data, Mapping):
                raise InventoryError(f"server '{name}' must be a mapping")
            host = data.get("host") or data.get("hostname") or name
            ssh = dict(data.get("ssh", {}))
            groups = tuple(data.get("groups", ()))
            server_vars = dict(data.get("vars", {}))
            target = Target(
                name=str(name),
                host=str(host),
                port=int(ssh.get("port", data.get("port", 22))),
                user=ssh.get("user") or data.get("user"),
                password=ssh.get("password") or data.get("password"),
                key_file=ssh.get("key_file") or data.get("key_file"),
                key_content=ssh.get("key_content") or data.get("key_content"),
                groups=groups,
                vars=server_vars,
                ssh=ssh,
            )
            servers[target.name] = target

        if not servers:
            raise InventoryError("inventory must contain at least one server")
        return servers

    @staticmethod
    def _parse_groups(
        document: Mapping[str, Any], targets: Mapping[str, Target]
    ) -> Dict[str, List[str]]:
        groups: Dict[str, List[str]] = {}
        for target in targets.values():
            for group in target.groups:
                groups.setdefault(group, []).append(target.name)

        raw_groups = document.get("groups", {})
        if not raw_groups:
            return groups
        if not isinstance(raw_groups, Mapping):
            raise InventoryError("inventory 'groups' must be a mapping")
        for group, members in raw_groups.items():
            if not isinstance(members, list):
                raise InventoryError(f"group '{group}' must be a list")
            groups.setdefault(str(group), [])
            for member in members:
                if member not in targets:
                    raise InventoryError(f"group '{group}' references unknown server: {member}")
                if member not in groups[str(group)]:
                    groups[str(group)].append(str(member))
        return groups
