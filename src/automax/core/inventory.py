"""
Inventory parsing and target selection.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence

from automax.core.models import Target
from automax.core.templating import render_mapping


class InventoryError(ValueError):
    """Raised when inventory cannot be parsed or resolved."""


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
