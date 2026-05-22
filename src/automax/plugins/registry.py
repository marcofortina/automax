"""
Explicit plugin registry.

Builtins are imported explicitly. Extra plugins can be loaded later from Python entry
points or external plugin paths without touching the engine.
"""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Iterable

from automax.plugins.base import BasePlugin


class PluginRegistryError(ValueError):
    """Raised when a plugin cannot be registered or found."""


class PluginRegistry:
    """Runtime plugin registry."""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._canonical_names: set[str] = set()

    def register(self, plugin: BasePlugin) -> None:
        """Register one plugin instance under its canonical name and optional aliases."""
        if plugin.name in self._plugins:
            raise PluginRegistryError(f"duplicate plugin name: {plugin.name}")
        self._plugins[plugin.name] = plugin
        self._canonical_names.add(plugin.name)
        for alias in plugin.aliases:
            if alias in self._plugins:
                raise PluginRegistryError(f"duplicate plugin alias: {alias}")
            self._plugins[alias] = plugin

    def get(self, name: str) -> BasePlugin:
        """Return a plugin by name."""
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise PluginRegistryError(f"unknown plugin: {name}") from exc

    def names(self, *, include_aliases: bool = False) -> list[str]:
        """List canonical plugin names, optionally including aliases."""
        if include_aliases:
            return sorted(self._plugins)
        return sorted(self._canonical_names)

    def load_from_paths(self, paths: Iterable[str]) -> None:
        """Load plugin classes from external .py files or directories."""
        for raw_path in paths:
            path = Path(raw_path).expanduser().resolve()
            if path.is_dir():
                for plugin_file in sorted(path.glob("*.py")):
                    self._load_module_file(plugin_file)
            elif path.is_file():
                self._load_module_file(path)
            else:
                raise PluginRegistryError(f"plugin path not found: {path}")

    def _load_module_file(self, path: Path) -> None:
        module_name = f"automax_external_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise PluginRegistryError(f"cannot load plugin module: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        found = False
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                self.register(obj())
                found = True
        if not found:
            raise PluginRegistryError(f"no BasePlugin subclasses found in: {path}")


def build_builtin_registry(extra_plugin_paths: Iterable[str] = ()) -> PluginRegistry:
    """Create a registry with builtin plugins and optional external plugins."""
    from automax.plugins.archive import (
        ArchiveTarPlugin,
        ArchiveUntarPlugin,
        ArchiveUnzipPlugin,
        ArchiveZipPlugin,
    )
    from automax.plugins.fs_cd import FsCdPlugin
    from automax.plugins.fs_chmod import FsChmodPlugin
    from automax.plugins.fs_chown import FsChownPlugin
    from automax.plugins.fs_copy import FsCopyPlugin
    from automax.plugins.fs_mkdir import FsMkdirPlugin
    from automax.plugins.fs_remove import FsRemovePlugin
    from automax.plugins.fs_extra import (
        FsExistsPlugin,
        FsFindPlugin,
        FsLinePlugin,
        FsMovePlugin,
        FsReadPlugin,
        FsReplacePlugin,
        FsStatPlugin,
        FsSymlinkPlugin,
        FsTemplatePlugin,
        FsWritePlugin,
    )
    from automax.plugins.local_command import LocalCommandPlugin
    from automax.plugins.pkg import (
        PackageInstallPlugin,
        PackageQueryPlugin,
        PackageRemovePlugin,
        PackageUpdateCachePlugin,
        PackageUpgradePlugin,
    )
    from automax.plugins.remote_command import RemoteCommandPlugin
    from automax.plugins.systemctl import (
        SystemctlDaemonReloadPlugin,
        SystemctlDisablePlugin,
        SystemctlEnablePlugin,
        SystemctlIsActivePlugin,
        SystemctlIsEnabledPlugin,
        SystemctlMaskPlugin,
        SystemctlReloadPlugin,
        SystemctlRestartPlugin,
        SystemctlStartPlugin,
        SystemctlStatusPlugin,
        SystemctlStopPlugin,
        SystemctlUnmaskPlugin,
    )

    registry = PluginRegistry()
    for plugin in (
        LocalCommandPlugin(),
        RemoteCommandPlugin(),
        PackageInstallPlugin(),
        PackageRemovePlugin(),
        PackageUpdateCachePlugin(),
        PackageUpgradePlugin(),
        PackageQueryPlugin(),
        FsCdPlugin(),
        FsMkdirPlugin(),
        FsCopyPlugin(),
        FsRemovePlugin(),
        FsExistsPlugin(),
        FsStatPlugin(),
        FsReadPlugin(),
        FsWritePlugin(),
        FsTemplatePlugin(),
        FsLinePlugin(),
        FsReplacePlugin(),
        FsMovePlugin(),
        FsSymlinkPlugin(),
        FsFindPlugin(),
        FsChownPlugin(),
        FsChmodPlugin(),
        ArchiveTarPlugin(),
        ArchiveUntarPlugin(),
        ArchiveZipPlugin(),
        ArchiveUnzipPlugin(),
        SystemctlStartPlugin(),
        SystemctlStopPlugin(),
        SystemctlRestartPlugin(),
        SystemctlReloadPlugin(),
        SystemctlEnablePlugin(),
        SystemctlDisablePlugin(),
        SystemctlStatusPlugin(),
        SystemctlIsActivePlugin(),
        SystemctlIsEnabledPlugin(),
        SystemctlMaskPlugin(),
        SystemctlUnmaskPlugin(),
        SystemctlDaemonReloadPlugin(),
    ):
        registry.register(plugin)
    registry.load_from_paths(extra_plugin_paths)
    return registry
