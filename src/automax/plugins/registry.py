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
    from automax.plugins.capabilities import CapabilityAssertPlugin, PluginRequirementsPlugin, ToolCheckPlugin, ToolVersionAssertPlugin
    from automax.plugins.block import (
        BlockFactsPlugin,
        BlockIdentityPlugin,
        BlockMkfsPlugin,
        BlockPartitionPlugin,
        BlockPartitionRescanPlugin,
        BlockRescanPlugin,
        BlockWipeSignaturesPlugin,
    )
    from automax.plugins.alternatives import AlternativesCheckPlugin, AlternativesGetPlugin, AlternativesListPlugin, AlternativesSetPlugin
    from automax.plugins.cert_ops import (
        CertExpiryReportPlugin,
        CertFingerprintPlugin,
        CertGenerateCsrPlugin,
        CertInstallCaBundlePlugin,
        CertInstallKeypairPlugin,
        CertIssuerAssertPlugin,
        CertMatchesKeyPlugin,
        CertSanAssertPlugin,
        CertSelfSignedPlugin,
        CertSubjectAssertPlugin,
        CertVerifyChainPlugin,
    )
    from automax.plugins.backup import (
        BackupDirectoryPlugin,
        BackupFilePlugin,
        BackupListPlugin,
        BackupManifestPlugin,
        BackupPrunePlugin,
        BackupRestorePlugin,
        BackupRestorePreviewPlugin,
        BackupRestoreVerifyPlugin,
        BackupRotatePlugin,
        BackupVerifyPlugin,
    )
    from automax.plugins.auditd import AuditdReloadPlugin, AuditdRulePlugin, AuditdStatusPlugin
    from automax.plugins.archive import (
        ArchiveTarCheckPlugin,
        ArchiveTarListPlugin,
        ArchiveTarPlugin,
        ArchiveZipCheckPlugin,
        ArchiveZipListPlugin,
        ArchiveZipPlugin,
        CompressionBzip2CheckPlugin,
        CompressionBzip2CompressPlugin,
        CompressionBzip2DecompressPlugin,
        CompressionGzipCheckPlugin,
        CompressionGzipCompressPlugin,
        CompressionGzipDecompressPlugin,
        CompressionXzCheckPlugin,
        CompressionXzCompressPlugin,
        CompressionXzDecompressPlugin,
        CompressionZstdCheckPlugin,
        CompressionZstdCompressPlugin,
        CompressionZstdDecompressPlugin,
        HardenedArchiveUntarPlugin,
        HardenedArchiveUnzipPlugin,
    )
    from automax.plugins.facts import (
        FactsOsPlugin,
        FactsPackagesPlugin,
        FactsServicesPlugin,
        OsArchCheckPlugin,
    )
    from automax.plugins.firewall import (
        FirewalldListPlugin,
        FirewalldReloadPlugin,
        FirewalldPortPlugin,
        FirewalldRichRulePlugin,
        FirewalldServicePlugin,
        FirewalldStatusPlugin,
        FirewalldZonePlugin,
        IptablesChainPlugin,
        IptablesListPlugin,
        IptablesPolicyPlugin,
        IptablesRestorePlugin,
        IptablesRulePlugin,
        IptablesSavePlugin,
        NftablesApplyPlugin,
        NftablesExportPlugin,
        NftablesListPlugin,
        NftablesValidatePlugin,
        UfwDisablePlugin,
        UfwEnablePlugin,
        UfwRulePlugin,
        UfwStatusPlugin,
    )
    from automax.plugins.fs_advanced import FsBindMountPlugin, FsInodeUsageAssertPlugin
    from automax.plugins.fs_chmod import FsChmodPlugin, FsModeCheckPlugin, FsModeGetPlugin
    from automax.plugins.fs_chown import FsChownPlugin, FsOwnerCheckPlugin, FsOwnerGetPlugin
    from automax.plugins.fs_copy import FsCopyPlugin
    from automax.plugins.fs_system import (
        FsAclAssertPlugin,
        FsAclGetPlugin,
        FsAclPlugin,
        FsAclRestorePlugin,
        FsAttrCheckPlugin,
        FsAttrGetPlugin,
        FsAttrPlugin,
        FsQuotaPlugin,
        StorageQuotaCheckPlugin,
        StorageQuotaFactsPlugin,
        StorageQuotaGetPlugin,
    )
    from automax.plugins.fs_extra import (
        FsFindPlugin,
        ExtendedFsLinePlugin,
        FsLineCheckPlugin,
        FsMovePlugin,
        FsReadPlugin,
        ExtendedFsReplacePlugin,
        FsStatPlugin,
        FsSymlinkCreatePlugin,
        FsSymlinkRemovePlugin,
        ExtendedFsTemplatePlugin,
        ExtendedFsWritePlugin,
    )
    from automax.plugins.cron import CronAbsentPlugin, CronEntryPlugin, CronFilePlugin, CronListPlugin, CronValidatePlugin
    from automax.plugins.db import (
        DatabaseMysqlCheckPlugin,
        DatabaseOracleCheckPlugin,
        DatabasePostgresCheckPlugin,
        DatabaseSqliteCheckPlugin,
        DbMysqlQueryPlugin,
        DbOracleQueryPlugin,
        DbPostgresQueryPlugin,
        DbSqliteQueryPlugin,
    )
    from automax.plugins.fs_typed import (
        FsDirCreatePlugin,
        FsDirCheckPlugin,
        FsDirRemovePlugin,
        FsDirWaitPlugin,
        FsFileCreatePlugin,
        FsFileCheckPlugin,
        FsFileRemovePlugin,
        FsFileWaitPlugin,
        FsSymlinkCheckPlugin,
        FsSymlinkGetPlugin,
        FsSymlinkWaitPlugin,
    )
    from automax.plugins.http import HttpAssertPlugin, HttpRequestPlugin, HttpWaitPlugin
    from automax.plugins.wait_assert import AssertDiskPlugin
    from automax.plugins.kernel import (
        KernelModuleLoadPlugin,
        KernelBootParamPlugin,
        KernelModulePersistPlugin,
        KernelModuleUnloadPlugin,
        SysctlGetPlugin,
        SysctlPersistPlugin,
        SysctlReloadPlugin,
        SysctlSetPlugin,
    )
    from automax.plugins.linux_ops import (
        ChronyServersPlugin,
        ChronyServersCheckPlugin,
        ChronyServersGetPlugin,
        ChronySourcesAssertPlugin,
        DownloadFilePlugin,
        EnvCheckPlugin,
        EnvFactsPlugin,
        EnvGetPlugin,
        EnvRemovePlugin,
        EnvSetPlugin,
        HostnameCheckPlugin,
        HostnameGetPlugin,
        HostnameSetPlugin,
        HostsEntryCheckPlugin,
        HostsEntryPlugin,
        HostsEntryRemovePlugin,
        HostsFactsPlugin,
        LimitsDropinPlugin,
        NetworkDnsFactsPlugin,
        PamLimitsPlugin,
        SwapAbsentPlugin,
        SwapPresentPlugin,
        SystemRebootPlugin,
    )
    from automax.plugins.lvm import (
        LvmLvExtendPlugin,
        LvmLvPresentPlugin,
        LvmLvRemovePlugin,
        LvmLvScanPlugin,
        LvmPvPresentPlugin,
        LvmPvRemovePlugin,
        LvmPvScanPlugin,
        LvmSnapshotPlugin,
        LvmThinPoolPlugin,
        LvmVgPresentPlugin,
        LvmVgRemovePlugin,
        LvmVgScanPlugin,
    )
    from automax.plugins.network import (
        NetworkBondPlugin,
        NetworkBridgePlugin,
        NetworkDnsCheckPlugin,
        NetworkDnsConfigPlugin,
        NetworkInterfacePlugin,
        NetworkLinkCheckPlugin,
        NetworkLinkFactsPlugin,
        NetworkPortCheckPlugin,
        NetworkPortWaitPlugin,
        NetworkRouteAddPlugin,
        NetworkRouteCheckPlugin,
        NetworkRouteFactsPlugin,
        NetworkRouteRemovePlugin,
        NetworkVlanPlugin,
    )
    from automax.plugins.hardening import AuthselectProfilePlugin, ExtendedSshdConfigPlugin, LoginDefsCheckPlugin, LoginDefsGetPlugin, LoginDefsPlugin, PasswordPolicyPlugin
    from automax.plugins.ops_completeness import (
        ApparmorComplainPlugin,
        ApparmorDisablePlugin,
        ApparmorEnforcePlugin,
        ApparmorParserValidatePlugin,
        ApparmorProfileAssertPlugin,
        AuditdBacklogAssertPlugin,
        AuditdRulesFactsPlugin,
        AuditdSearchPlugin,
        AuditdSyscallPlugin,
        AuditdWatchPlugin,
        BlockEmptyAssertPlugin,
        BlockMountpointAssertPlugin,
        BlockNotMountedAssertPlugin,
        BlockSizeAssertPlugin,
        ChronyTrackingAssertPlugin,
        FirewalldForwardPortPlugin,
        FirewalldIcmpBlockPlugin,
        FirewalldMasqueradePlugin,
        FirewalldSourcePlugin,
        FstabAbsentPlugin,
        FstabAssertPlugin,
        GroupMemberAbsentPlugin,
        GroupMemberAddPlugin,
        GroupMemberCheckPlugin,
        GroupMembersPlugin,
        IptablesCounterCheckPlugin,
        IptablesDeletePlugin,
        IptablesRuleCheckPlugin,
        KernelBootParamAbsentPlugin,
        KernelBootParamCheckPlugin,
        KernelModuleBlacklistPlugin,
        KernelModuleStatusPlugin,
        NftablesRollbackFilePlugin,
        NftablesRulesetCheckPlugin,
        PamBackupPlugin,
        PamIncludeAssertPlugin,
        PamModuleAssertPlugin,
        PamOrderAssertPlugin,
        PamRestorePlugin,
        SudoAssertPlugin,
        SudoCanRunPlugin,
        SudoListPlugin,
        SysctlAssertPlugin,
        SysctlDropinPlugin,
        SysctlFactsPlugin,
        TimedatectlNtpCheckPlugin,
        TimedatectlNtpGetPlugin,
        TimedatectlNtpPlugin,
        TimedatectlStatusPlugin,
        TimedatectlTimezoneCheckPlugin,
        TimedatectlTimezoneGetPlugin,
        TimedatectlTimezonePlugin,
        UdevFactsPlugin,
        UdevTestPlugin,
        UdevValidatePlugin,
        UfwDeletePlugin,
        UfwResetPlugin,
        UserFactsPlugin,
        UserGroupsAssertPlugin,
        UserHomeAssertPlugin,
        UserShellAssertPlugin,
    )
    from automax.plugins.pam_ops import (
        PamAccessPlugin,
        PamAuthselectPlugin,
        PamFaillockPlugin,
        PamPwhistoryPlugin,
        PamServiceLinePlugin,
        PamStackFactsPlugin,
        PamSucceedIfPlugin,
        PamValidatePlugin,
    )
    from automax.plugins.pki import (
        PkiCaInstallPlugin,
        PkiCertExpiryAssertPlugin,
        PkiKeyPermissionsPlugin,
    )
    from automax.plugins.platform import PlatformFactsPlugin
    from automax.plugins.pkg_pinning import (
        PkgHoldCheckPlugin,
        PkgHoldListPlugin,
        PkgHoldPlugin,
        PkgRepoPriorityCheckPlugin,
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
        MultipathAddPlugin,
        MultipathFlushPlugin,
        MultipathReloadPlugin,
        MultipathStatusPlugin,
    )
    from automax.plugins.udev import (
        UdevReloadPlugin,
        UdevRuleCheckPlugin,
        UdevRulePlugin,
        UdevRuleRemovePlugin,
        UdevSettlePlugin,
        UdevTriggerPlugin,
    )
    from automax.plugins.mounts import (
        FstabEntryPlugin,
        MountAbsentPlugin,
        MountPresentPlugin,
    )
    from automax.plugins.pkg import (
        PackageCheckPlugin,
        PackageCleanPlugin,
        PackageFilesPlugin,
        ExtendedPackageInstallPlugin,
        PackageOwnerPlugin,
        PackageQueryPlugin,
        ExtendedPackageRemovePlugin,
        PackageUpdateCachePlugin,
        ExtendedPackageUpgradePlugin,
        PackageVerifyPlugin,
        PackageVersionAssertPlugin,
    )
    from automax.plugins.pkg_repo import (
        PackageKeyAddPlugin,
        PackageKeyCheckPlugin,
        PackageKeyListPlugin,
        PackageKeyRemovePlugin,
        PackageRepoAddPlugin,
        PackageRepoCheckPlugin,
        PackageRepoListPlugin,
        PackageRepoRemovePlugin,
    )
    from automax.plugins.redaction import SecretRedactAssertPlugin, SecretScanOutputPlugin, SecretScanPreviewPlugin
    from automax.plugins.remote_command import RemoteCommandPlugin
    from automax.plugins.transfer import (
        TransferDownloadPlugin,
        ExtendedTransferRsyncPlugin,
        TransferUploadPlugin,
    )
    from automax.plugins.users_extra import (
        GroupCheckPlugin,
        ExtendedSshAuthorizedKeyPlugin,
        SudoersDropinPlugin,
        UserCheckPlugin,
        UserLockPlugin,
        UserSetPasswordPlugin,
        UserUnlockPlugin,
    )
    from automax.plugins.user_group_process import (
        GroupCreatePlugin,
        GroupRemovePlugin,
        ProcessCheckPlugin,
        ProcessAssertCountPlugin,
        ProcessKillPlugin,
        ProcessSignalPlugin,
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
    from automax.plugins.sudo_ops import SudoRulePlugin, SudoValidatePlugin
    from automax.plugins.ssh_ops import (
        SshAuthorizedKeyAbsentPlugin,
        SshConfigPlugin,
        SshFingerprintPlugin,
        SshHostKeygenPlugin,
        ExtendedSshKeygenPlugin,
        SshKnownHostsPlugin,
        SshPublicKeyPlugin,
        SshdValidatePlugin,
    )
    from automax.plugins.systemd_resources import SystemdSysusersPlugin, SystemdTimerPlugin, SystemdTmpfilesPlugin, SystemdUnitPlugin
    from automax.plugins.storage_readback import (
        BlkidAssertPlugin,
        FstabValidatePlugin,
        LvmFactsPlugin,
        LvmLvAssertPlugin,
        MountFactsPlugin,
        StorageFsFactsPlugin,
        StorageSwapCheckPlugin,
        SwapStatusPlugin,
    )
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
        AlternativesGetPlugin(),
        AlternativesListPlugin(),
        AlternativesCheckPlugin(),
        ToolCheckPlugin(),
        ToolVersionAssertPlugin(),
        CapabilityAssertPlugin(),
        PluginRequirementsPlugin(),
        AlternativesSetPlugin(),
        BackupFilePlugin(),
        BackupDirectoryPlugin(),
        BackupRestorePlugin(),
        BackupVerifyPlugin(),
        BackupListPlugin(),
        BackupManifestPlugin(),
        BackupPrunePlugin(),
        BackupRotatePlugin(),
        BackupRestorePreviewPlugin(),
        BackupRestoreVerifyPlugin(),
        CertExpiryReportPlugin(),
        CertGenerateCsrPlugin(),
        CertInstallKeypairPlugin(),
        CertSelfSignedPlugin(),
        CertVerifyChainPlugin(),
        CertFingerprintPlugin(),
        CertMatchesKeyPlugin(),
        CertSanAssertPlugin(),
        CertSubjectAssertPlugin(),
        CertIssuerAssertPlugin(),
        CertInstallCaBundlePlugin(),
        HttpRequestPlugin(),
        HttpAssertPlugin(),
        HttpWaitPlugin(),
        DatabaseSqliteCheckPlugin(),
        DatabasePostgresCheckPlugin(),
        DatabaseMysqlCheckPlugin(),
        DatabaseOracleCheckPlugin(),
        DbSqliteQueryPlugin(),
        DbPostgresQueryPlugin(),
        DbMysqlQueryPlugin(),
        DbOracleQueryPlugin(),
        CronEntryPlugin(),
        CronFilePlugin(),
        CronListPlugin(),
        CronAbsentPlugin(),
        CronValidatePlugin(),
        FactsOsPlugin(),
        OsArchCheckPlugin(),
        FactsPackagesPlugin(),
        FactsServicesPlugin(),
        PlatformFactsPlugin(),
        AssertDiskPlugin(),
        FirewalldPortPlugin(),
        FirewalldServicePlugin(),
        FirewalldSourcePlugin(),
        FirewalldIcmpBlockPlugin(),
        FirewalldMasqueradePlugin(),
        FirewalldForwardPortPlugin(),
        FirewalldRichRulePlugin(),
        FirewalldReloadPlugin(),
        FirewalldStatusPlugin(),
        FirewalldListPlugin(),
        FirewalldZonePlugin(),
        IptablesRestorePlugin(),
        IptablesRulePlugin(),
        IptablesSavePlugin(),
        IptablesDeletePlugin(),
        IptablesRuleCheckPlugin(),
        IptablesCounterCheckPlugin(),
        IptablesListPlugin(),
        IptablesPolicyPlugin(),
        IptablesChainPlugin(),
        UfwRulePlugin(),
        UfwStatusPlugin(),
        UfwEnablePlugin(),
        UfwDisablePlugin(),
        UfwDeletePlugin(),
        UfwResetPlugin(),
        NftablesValidatePlugin(),
        NftablesApplyPlugin(),
        NftablesListPlugin(),
        NftablesExportPlugin(),
        NftablesRulesetCheckPlugin(),
        NftablesRollbackFilePlugin(),
        SysctlGetPlugin(),
        SysctlSetPlugin(),
        SysctlPersistPlugin(),
        SysctlReloadPlugin(),
        SysctlAssertPlugin(),
        SysctlFactsPlugin(),
        SysctlDropinPlugin(),
        KernelBootParamPlugin(),
        KernelBootParamAbsentPlugin(),
        KernelBootParamCheckPlugin(),
        KernelModuleLoadPlugin(),
        KernelModuleStatusPlugin(),
        KernelModuleBlacklistPlugin(),
        KernelModuleUnloadPlugin(),
        KernelModulePersistPlugin(),
        MountPresentPlugin(),
        MountAbsentPlugin(),
        FstabEntryPlugin(),
        FstabAbsentPlugin(),
        FstabAssertPlugin(),
        SelinuxModePlugin(),
        SelinuxBooleanPlugin(),
        SelinuxContextPlugin(),
        SelinuxFcontextPlugin(),
        SelinuxPortPlugin(),
        SelinuxRestoreconPlugin(),
        ApparmorStatusPlugin(),
        ApparmorProfilePlugin(),
        ApparmorReloadPlugin(),
        ApparmorEnforcePlugin(),
        ApparmorComplainPlugin(),
        ApparmorDisablePlugin(),
        ApparmorProfileAssertPlugin(),
        ApparmorParserValidatePlugin(),
        AuditdRulePlugin(),
        AuditdStatusPlugin(),
        AuditdReloadPlugin(),
        AuditdRulesFactsPlugin(),
        AuditdWatchPlugin(),
        AuditdSyscallPlugin(),
        AuditdSearchPlugin(),
        AuditdBacklogAssertPlugin(),
        SecretRedactAssertPlugin(),
        SecretScanOutputPlugin(),
        SecretScanPreviewPlugin(),
        RemoteCommandPlugin(),
        ExtendedPackageInstallPlugin(),
        ExtendedPackageRemovePlugin(),
        PackageUpdateCachePlugin(),
        ExtendedPackageUpgradePlugin(),
        PackageQueryPlugin(),
        PackageCheckPlugin(),
        PackageVersionAssertPlugin(),
        PackageOwnerPlugin(),
        PackageFilesPlugin(),
        PackageVerifyPlugin(),
        PackageCleanPlugin(),
        PackageKeyAddPlugin(),
        PackageKeyListPlugin(),
        PackageKeyCheckPlugin(),
        PackageKeyRemovePlugin(),
        PackageRepoAddPlugin(),
        PackageRepoListPlugin(),
        PackageRepoCheckPlugin(),
        PackageRepoRemovePlugin(),
        UserCreatePlugin(),
        UserModifyPlugin(),
        UserFactsPlugin(),
        UserShellAssertPlugin(),
        UserHomeAssertPlugin(),
        UserGroupsAssertPlugin(),
        UserRemovePlugin(),
        UserCheckPlugin(),
        UserLockPlugin(),
        UserUnlockPlugin(),
        UserSetPasswordPlugin(),
        GroupCreatePlugin(),
        GroupRemovePlugin(),
        GroupCheckPlugin(),
        GroupMembersPlugin(),
        GroupMemberAddPlugin(),
        GroupMemberCheckPlugin(),
        GroupMemberAbsentPlugin(),
        ExtendedSshAuthorizedKeyPlugin(),
        ExtendedSshdConfigPlugin(),
        LoginDefsPlugin(),
        LoginDefsGetPlugin(),
        LoginDefsCheckPlugin(),
        PasswordPolicyPlugin(),
        AuthselectProfilePlugin(),
        SshConfigPlugin(),
        ExtendedSshKeygenPlugin(),
        SshKnownHostsPlugin(),
        SshFingerprintPlugin(),
        SshPublicKeyPlugin(),
        SshHostKeygenPlugin(),
        SshAuthorizedKeyAbsentPlugin(),
        SshdValidatePlugin(),
        SudoersDropinPlugin(),
        SudoRulePlugin(),
        SudoValidatePlugin(),
        SudoListPlugin(),
        SudoAssertPlugin(),
        SudoCanRunPlugin(),
        ProcessCheckPlugin(),
        ProcessAssertCountPlugin(),
        ProcessKillPlugin(),
        ProcessSignalPlugin(),
        ProcessWaitPlugin(),
        TransferUploadPlugin(),
        TransferDownloadPlugin(),
        ExtendedTransferRsyncPlugin(),
        FsDirCreatePlugin(),
        FsDirRemovePlugin(),
        FsDirCheckPlugin(),
        FsDirWaitPlugin(),
        FsFileCreatePlugin(),
        FsFileRemovePlugin(),
        FsFileCheckPlugin(),
        FsFileWaitPlugin(),
        FsCopyPlugin(),
        FsStatPlugin(),
        FsReadPlugin(),
        ExtendedFsWritePlugin(),
        ExtendedFsTemplatePlugin(),
        ExtendedFsLinePlugin(),
        FsLineCheckPlugin(),
        ExtendedFsReplacePlugin(),
        FsMovePlugin(),
        FsSymlinkCreatePlugin(),
        FsSymlinkRemovePlugin(),
        FsSymlinkCheckPlugin(),
        FsSymlinkGetPlugin(),
        FsSymlinkWaitPlugin(),
        FsFindPlugin(),
        FsOwnerCheckPlugin(),
        FsOwnerGetPlugin(),
        FsChownPlugin(),
        FsModeCheckPlugin(),
        FsModeGetPlugin(),
        FsChmodPlugin(),
        FsAclPlugin(),
        FsAclGetPlugin(),
        FsAclAssertPlugin(),
        FsAclRestorePlugin(),
        FsBindMountPlugin(),
        FsInodeUsageAssertPlugin(),
        FsAttrPlugin(),
        FsAttrGetPlugin(),
        FsAttrCheckPlugin(),
        FsQuotaPlugin(),
        StorageQuotaGetPlugin(),
        StorageQuotaCheckPlugin(),
        StorageQuotaFactsPlugin(),
        BlockFactsPlugin(),
        BlockIdentityPlugin(),
        BlockRescanPlugin(),
        BlockSizeAssertPlugin(),
        BlockMountpointAssertPlugin(),
        BlockEmptyAssertPlugin(),
        BlockNotMountedAssertPlugin(),
        BlockPartitionRescanPlugin(),
        BlockPartitionPlugin(),
        BlockWipeSignaturesPlugin(),
        BlockMkfsPlugin(),
        UdevRulePlugin(),
        UdevRuleRemovePlugin(),
        UdevRuleCheckPlugin(),
        UdevReloadPlugin(),
        UdevTriggerPlugin(),
        UdevSettlePlugin(),
        UdevValidatePlugin(),
        UdevTestPlugin(),
        UdevFactsPlugin(),
        MultipathStatusPlugin(),
        MultipathReloadPlugin(),
        MultipathAddPlugin(),
        MultipathFlushPlugin(),
        SwapPresentPlugin(),
        SwapAbsentPlugin(),
        LimitsDropinPlugin(),
        PamLimitsPlugin(),
        PamAccessPlugin(),
        PamIncludeAssertPlugin(),
        PamModuleAssertPlugin(),
        PamOrderAssertPlugin(),
        PamBackupPlugin(),
        PamRestorePlugin(),
        PamFaillockPlugin(),
        PamPwhistoryPlugin(),
        PamSucceedIfPlugin(),
        PamServiceLinePlugin(),
        PamValidatePlugin(),
        PamStackFactsPlugin(),
        PamAuthselectPlugin(),
        HostsEntryPlugin(),
        HostsEntryRemovePlugin(),
        HostsEntryCheckPlugin(),
        HostsFactsPlugin(),
        HostnameSetPlugin(),
        HostnameGetPlugin(),
        HostnameCheckPlugin(),
        NetworkDnsFactsPlugin(),
        ChronyServersPlugin(),
        ChronyServersGetPlugin(),
        ChronyServersCheckPlugin(),
        ChronySourcesAssertPlugin(),
        ChronyTrackingAssertPlugin(),
        TimedatectlStatusPlugin(),
        TimedatectlTimezonePlugin(),
        TimedatectlTimezoneGetPlugin(),
        TimedatectlTimezoneCheckPlugin(),
        TimedatectlNtpPlugin(),
        TimedatectlNtpGetPlugin(),
        TimedatectlNtpCheckPlugin(),
        EnvSetPlugin(),
        EnvGetPlugin(),
        EnvCheckPlugin(),
        EnvFactsPlugin(),
        EnvRemovePlugin(),
        SystemRebootPlugin(),
        DownloadFilePlugin(),
        LvmPvPresentPlugin(),
        LvmVgPresentPlugin(),
        LvmLvPresentPlugin(),
        LvmFactsPlugin(),
        LvmLvAssertPlugin(),
        LvmLvExtendPlugin(),
        LvmLvScanPlugin(),
        LvmSnapshotPlugin(),
        LvmThinPoolPlugin(),
        LvmLvRemovePlugin(),
        LvmVgRemovePlugin(),
        LvmVgScanPlugin(),
        LvmPvRemovePlugin(),
        LvmPvScanPlugin(),
        NetworkInterfacePlugin(),
        NetworkRouteAddPlugin(),
        NetworkRouteRemovePlugin(),
        NetworkRouteFactsPlugin(),
        NetworkBondPlugin(),
        NetworkVlanPlugin(),
        NetworkDnsConfigPlugin(),
        NetworkBridgePlugin(),
        NetworkLinkCheckPlugin(),
        NetworkLinkFactsPlugin(),
        NetworkRouteCheckPlugin(),
        NetworkDnsCheckPlugin(),
        NetworkPortCheckPlugin(),
        NetworkPortWaitPlugin(),
        PkiCaInstallPlugin(),
        PkiKeyPermissionsPlugin(),
        PkiCertExpiryAssertPlugin(),
        PkgHoldPlugin(),
        PkgUnholdPlugin(),
        PkgHoldListPlugin(),
        PkgHoldCheckPlugin(),
        PkgVersionPinPlugin(),
        PkgRepoPriorityPlugin(),
        PkgRepoPriorityCheckPlugin(),
        MountRemountPlugin(),
        MountFactsPlugin(),
        FstabValidatePlugin(),
        SwapStatusPlugin(),
        StorageSwapCheckPlugin(),
        BlkidAssertPlugin(),
        StorageFsFactsPlugin(),
        FsResizePlugin(),
        FindmntAssertPlugin(),
        LogGrepPlugin(),
        JournalCollectPlugin(),
        JournalGrepPlugin(),
        LogExportPlugin(),
        MailSendPlugin(),
        ArchiveTarPlugin(),
        HardenedArchiveUntarPlugin(),
        ArchiveTarListPlugin(),
        ArchiveTarCheckPlugin(),
        ArchiveZipPlugin(),
        HardenedArchiveUnzipPlugin(),
        ArchiveZipListPlugin(),
        ArchiveZipCheckPlugin(),
        CompressionGzipCompressPlugin(),
        CompressionGzipDecompressPlugin(),
        CompressionGzipCheckPlugin(),
        CompressionBzip2CompressPlugin(),
        CompressionBzip2DecompressPlugin(),
        CompressionBzip2CheckPlugin(),
        CompressionXzCompressPlugin(),
        CompressionXzDecompressPlugin(),
        CompressionXzCheckPlugin(),
        CompressionZstdCompressPlugin(),
        CompressionZstdDecompressPlugin(),
        CompressionZstdCheckPlugin(),
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
