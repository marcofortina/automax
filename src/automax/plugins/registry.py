# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

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
from automax.plugins.metadata import apply_builtin_metadata


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

    def describe(self, name: str) -> dict[str, object]:
        """Return user-facing metadata for one plugin."""
        return self.get(name).metadata()

    def describe_all(self) -> list[dict[str, object]]:
        """Return metadata for all canonical plugins."""
        return [self.get(name).metadata() for name in self.names()]

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
    from automax.plugins.block import (
        BlockFactsPlugin,
        BlockIdentityPlugin,
        BlockMkfsPlugin,
        BlockPartitionPlugin,
        BlockPartitionRescanPlugin,
        BlockRescanPlugin,
        BlockWipeSignaturesPlugin,
    )
    from automax.plugins.alternatives import AlternativesSetPlugin
    from automax.plugins.auditd import AuditdReloadPlugin, AuditdRulePlugin, AuditdStatusPlugin
    from automax.plugins.archive import (
        ArchiveCompressPlugin,
        ArchiveDecompressPlugin,
        ArchiveTarPlugin,
        ArchiveUntarPlugin,
        ArchiveUnzipPlugin,
        ArchiveZipPlugin,
    )
    from automax.plugins.facts import (
        FactsGatherPlugin,
        FactsNetworkPlugin,
        FactsOsPlugin,
        FactsPackagesPlugin,
        FactsServicesPlugin,
    )
    from automax.plugins.firewall import (
        FirewalldPortPlugin,
        FirewalldReloadPlugin,
        FirewalldRichRulePlugin,
        FirewalldServicePlugin,
        NftablesApplyPlugin,
        NftablesValidatePlugin,
        UfwDisablePlugin,
        UfwEnablePlugin,
        UfwRulePlugin,
        UfwStatusPlugin,
    )
    from automax.plugins.fs_cd import FsCdPlugin
    from automax.plugins.fs_chmod import FsChmodPlugin
    from automax.plugins.fs_chown import FsChownPlugin
    from automax.plugins.fs_copy import FsCopyPlugin
    from automax.plugins.fs_mkdir import FsMkdirPlugin
    from automax.plugins.fs_remove import FsRemovePlugin
    from automax.plugins.fs_system import FsAclPlugin, FsAttrPlugin, FsQuotaPlugin
    from automax.plugins.fs_extra import (
        FsExistsPlugin,
        FsFindPlugin,
        FsLinePlugin,
        FsMovePlugin,
        FsReadPlugin,
        FsReplacePlugin,
        FsStatPlugin,
        FsSymlinkCreatePlugin,
        FsSymlinkRemovePlugin,
        FsTemplatePlugin,
        FsWritePlugin,
    )
    from automax.plugins.cron import CronEntryPlugin, CronFilePlugin
    from automax.plugins.db import (
        DbMysqlQueryPlugin,
        DbOracleQueryPlugin,
        DbPostgresQueryPlugin,
        DbSqliteQueryPlugin,
    )
    from automax.plugins.http import HttpAssertPlugin, HttpRequestPlugin, HttpWaitPlugin
    from automax.plugins.wait_assert import (
        AssertCommandPlugin,
        AssertDiskPlugin,
        AssertFilePlugin,
        AssertPathPlugin,
        AssertTcpPlugin,
        WaitCommandPlugin,
        WaitFilePlugin,
        WaitPathPlugin,
        WaitProcessPlugin,
        WaitTcpPlugin,
    )
    from automax.plugins.kernel import (
        KernelModuleLoadPlugin,
        KernelModulePersistPlugin,
        KernelModuleUnloadPlugin,
        SysctlGetPlugin,
        SysctlPersistPlugin,
        SysctlReloadPlugin,
        SysctlSetPlugin,
    )
    from automax.plugins.linux_ops import (
        ChronyServersPlugin,
        ChronySourcesAssertPlugin,
        DownloadFilePlugin,
        EnvSetPlugin,
        HostnameSetPlugin,
        HostsEntryPlugin,
        LimitsDropinPlugin,
        PamLimitsPlugin,
        ResolverConfigPlugin,
        ResolverFactsPlugin,
        SwapAbsentPlugin,
        SwapPresentPlugin,
        SystemRebootPlugin,
    )
    from automax.plugins.lvm import (
        LvmLvExtendPlugin,
        LvmLvPresentPlugin,
        LvmLvRemovePlugin,
        LvmPvPresentPlugin,
        LvmPvRemovePlugin,
        LvmResizeFsPlugin,
        LvmSnapshotPlugin,
        LvmThinPoolPlugin,
        LvmVgPresentPlugin,
        LvmVgRemovePlugin,
    )
    from automax.plugins.network import (
        NetworkBondPlugin,
        NetworkDnsPlugin,
        NetworkInterfacePlugin,
        NetworkRoutePlugin,
        NetworkVlanPlugin,
    )
    from automax.plugins.health import (
        HealthHttpPlugin,
        HealthListenPlugin,
        HealthPortPlugin,
        HealthProcessPlugin,
    )
    from automax.plugins.pki import (
        PkiCaInstallPlugin,
        PkiCertExpiryAssertPlugin,
        PkiKeyPermissionsPlugin,
    )
    from automax.plugins.platform import PlatformFactsPlugin
    from automax.plugins.pkg_pinning import (
        PkgHoldPlugin,
        PkgRepoPriorityPlugin,
        PkgUnholdPlugin,
        PkgVersionPinPlugin,
    )
    from automax.plugins.mounts_extra import (
        FindmntAssertPlugin,
        FsResizePlugin,
        MountRemountPlugin,
    )
    from automax.plugins.logs import (
        JournalCollectPlugin,
        JournalGrepPlugin,
        LogExportPlugin,
        LogGrepPlugin,
    )
    from automax.plugins.mail import MailSendPlugin
    from automax.plugins.local_command import LocalCommandPlugin
    from automax.plugins.multipath import (
        MultipathFlushPlugin,
        MultipathReloadPlugin,
        MultipathStatusPlugin,
    )
    from automax.plugins.udev import (
        UdevReloadPlugin,
        UdevRulePlugin,
        UdevSettlePlugin,
        UdevTriggerPlugin,
    )
    from automax.plugins.mounts import (
        FstabEntryPlugin,
        MountAbsentPlugin,
        MountPresentPlugin,
    )
    from automax.plugins.pkg import (
        PackageInstallPlugin,
        PackageQueryPlugin,
        PackageRemovePlugin,
        PackageUpdateCachePlugin,
        PackageUpgradePlugin,
    )
    from automax.plugins.pkg_repo import (
        PackageKeyAddPlugin,
        PackageKeyRemovePlugin,
        PackageRepoAddPlugin,
        PackageRepoRemovePlugin,
    )
    from automax.plugins.remote_command import RemoteCommandPlugin
    from automax.plugins.transfer import (
        TransferDownloadPlugin,
        TransferSyncPlugin,
        TransferUploadPlugin,
    )
    from automax.plugins.users_extra import (
        GroupExistsPlugin,
        SshAuthorizedKeyPlugin,
        SudoersDropinPlugin,
        UserExistsPlugin,
        UserLockPlugin,
        UserSetPasswordPlugin,
        UserUnlockPlugin,
    )
    from automax.plugins.user_group_process import (
        GroupCreatePlugin,
        GroupRemovePlugin,
        ProcessKillPlugin,
        ProcessWaitPlugin,
        UserCreatePlugin,
        UserModifyPlugin,
        UserRemovePlugin,
    )
    from automax.plugins.security_modules import (
        ApparmorProfilePlugin,
        ApparmorReloadPlugin,
        ApparmorStatusPlugin,
        SelinuxBooleanPlugin,
        SelinuxContextPlugin,
        SelinuxFcontextPlugin,
        SelinuxModePlugin,
        SelinuxPortPlugin,
        SelinuxRestoreconPlugin,
    )
    from automax.plugins.ssh_ops import SshConfigPlugin, SshKnownHostsPlugin
    from automax.plugins.systemd_resources import SystemdSysusersPlugin, SystemdTimerPlugin, SystemdTmpfilesPlugin, SystemdUnitPlugin
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
        AlternativesSetPlugin(),
        HttpRequestPlugin(),
        HttpAssertPlugin(),
        HttpWaitPlugin(),
        DbSqliteQueryPlugin(),
        DbPostgresQueryPlugin(),
        DbMysqlQueryPlugin(),
        DbOracleQueryPlugin(),
        CronEntryPlugin(),
        CronFilePlugin(),
        FactsGatherPlugin(),
        FactsOsPlugin(),
        FactsNetworkPlugin(),
        FactsPackagesPlugin(),
        FactsServicesPlugin(),
        PlatformFactsPlugin(),
        WaitTcpPlugin(),
        WaitCommandPlugin(),
        WaitFilePlugin(),
        WaitPathPlugin(),
        WaitProcessPlugin(),
        AssertTcpPlugin(),
        AssertCommandPlugin(),
        AssertFilePlugin(),
        AssertPathPlugin(),
        AssertDiskPlugin(),
        FirewalldPortPlugin(),
        FirewalldServicePlugin(),
        FirewalldRichRulePlugin(),
        FirewalldReloadPlugin(),
        UfwRulePlugin(),
        UfwStatusPlugin(),
        UfwEnablePlugin(),
        UfwDisablePlugin(),
        NftablesValidatePlugin(),
        NftablesApplyPlugin(),
        SysctlGetPlugin(),
        SysctlSetPlugin(),
        SysctlPersistPlugin(),
        SysctlReloadPlugin(),
        KernelModuleLoadPlugin(),
        KernelModuleUnloadPlugin(),
        KernelModulePersistPlugin(),
        MountPresentPlugin(),
        MountAbsentPlugin(),
        FstabEntryPlugin(),
        SelinuxModePlugin(),
        SelinuxBooleanPlugin(),
        SelinuxContextPlugin(),
        SelinuxFcontextPlugin(),
        SelinuxPortPlugin(),
        SelinuxRestoreconPlugin(),
        ApparmorStatusPlugin(),
        ApparmorProfilePlugin(),
        ApparmorReloadPlugin(),
        AuditdRulePlugin(),
        AuditdStatusPlugin(),
        AuditdReloadPlugin(),
        RemoteCommandPlugin(),
        PackageInstallPlugin(),
        PackageRemovePlugin(),
        PackageUpdateCachePlugin(),
        PackageUpgradePlugin(),
        PackageQueryPlugin(),
        PackageKeyAddPlugin(),
        PackageKeyRemovePlugin(),
        PackageRepoAddPlugin(),
        PackageRepoRemovePlugin(),
        UserCreatePlugin(),
        UserModifyPlugin(),
        UserRemovePlugin(),
        UserExistsPlugin(),
        UserLockPlugin(),
        UserUnlockPlugin(),
        UserSetPasswordPlugin(),
        GroupCreatePlugin(),
        GroupRemovePlugin(),
        GroupExistsPlugin(),
        SshAuthorizedKeyPlugin(),
        SshConfigPlugin(),
        SshKnownHostsPlugin(),
        SudoersDropinPlugin(),
        ProcessKillPlugin(),
        ProcessWaitPlugin(),
        TransferUploadPlugin(),
        TransferDownloadPlugin(),
        TransferSyncPlugin(),
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
        FsSymlinkCreatePlugin(),
        FsSymlinkRemovePlugin(),
        FsFindPlugin(),
        FsChownPlugin(),
        FsChmodPlugin(),
        FsAclPlugin(),
        FsAttrPlugin(),
        FsQuotaPlugin(),
        BlockFactsPlugin(),
        BlockIdentityPlugin(),
        BlockRescanPlugin(),
        BlockPartitionRescanPlugin(),
        BlockPartitionPlugin(),
        BlockWipeSignaturesPlugin(),
        BlockMkfsPlugin(),
        UdevRulePlugin(),
        UdevReloadPlugin(),
        UdevTriggerPlugin(),
        UdevSettlePlugin(),
        MultipathStatusPlugin(),
        MultipathReloadPlugin(),
        MultipathFlushPlugin(),
        SwapPresentPlugin(),
        SwapAbsentPlugin(),
        LimitsDropinPlugin(),
        PamLimitsPlugin(),
        HostsEntryPlugin(),
        HostnameSetPlugin(),
        ResolverConfigPlugin(),
        ResolverFactsPlugin(),
        ChronyServersPlugin(),
        ChronySourcesAssertPlugin(),
        EnvSetPlugin(),
        SystemRebootPlugin(),
        DownloadFilePlugin(),
        LvmPvPresentPlugin(),
        LvmVgPresentPlugin(),
        LvmLvPresentPlugin(),
        LvmLvExtendPlugin(),
        LvmSnapshotPlugin(),
        LvmThinPoolPlugin(),
        LvmLvRemovePlugin(),
        LvmResizeFsPlugin(),
        LvmVgRemovePlugin(),
        LvmPvRemovePlugin(),
        NetworkInterfacePlugin(),
        NetworkRoutePlugin(),
        NetworkBondPlugin(),
        NetworkVlanPlugin(),
        NetworkDnsPlugin(),
        HealthPortPlugin(),
        HealthListenPlugin(),
        HealthProcessPlugin(),
        HealthHttpPlugin(),
        PkiCaInstallPlugin(),
        PkiKeyPermissionsPlugin(),
        PkiCertExpiryAssertPlugin(),
        PkgHoldPlugin(),
        PkgUnholdPlugin(),
        PkgVersionPinPlugin(),
        PkgRepoPriorityPlugin(),
        MountRemountPlugin(),
        FsResizePlugin(),
        FindmntAssertPlugin(),
        LogGrepPlugin(),
        JournalCollectPlugin(),
        JournalGrepPlugin(),
        LogExportPlugin(),
        MailSendPlugin(),
        ArchiveTarPlugin(),
        ArchiveUntarPlugin(),
        ArchiveCompressPlugin(),
        ArchiveDecompressPlugin(),
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
        SystemdUnitPlugin(),
        SystemdTimerPlugin(),
        SystemdTmpfilesPlugin(),
        SystemdSysusersPlugin(),
    ):
        registry.register(apply_builtin_metadata(plugin))
    registry.load_from_paths(extra_plugin_paths)
    return registry
