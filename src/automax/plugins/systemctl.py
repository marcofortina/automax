# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Remote systemctl macro plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote, sudo_command


def _systemctl_prefix(params: Dict[str, Any]) -> str:
    prefix = "systemctl --user" if bool(params.get("user", False)) else "systemctl"
    return sudo_command(params, prefix, default=False)


class _SystemctlServicePlugin(BasePlugin):
    """Base class for service-level systemctl plugins."""

    required_params = ("service",)
    optional_params = ("sudo", "user")
    opens_remote_session = True
    action = ""

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: systemctl {self.action} {params.get('service')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message=f"{self.name} requires an SSH session")
        command = self._build_command(params)
        rc, out, err = exec_remote(context, command)
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message=f"{self.name} failed",
            data={"service": params["service"], "action": self.action},
        )

    def _build_command(self, params: Dict[str, Any]) -> str:
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        return f"{systemctl} {self.action} {service} && echo {CHANGE_MARKER}"


class SystemctlStartPlugin(_SystemctlServicePlugin):
    """Start a service only when it is not already active."""

    name = "system.service.start"
    description = "Start a remote systemd service."
    action = "start"

    def _build_command(self, params: Dict[str, Any]) -> str:
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        return (
            f"{systemctl} is-active --quiet {service} "
            f"|| {{ {systemctl} start {service} && echo {CHANGE_MARKER}; }}"
        )


class SystemctlStopPlugin(_SystemctlServicePlugin):
    """Stop a service only when it is active."""

    name = "system.service.stop"
    description = "Stop a remote systemd service."
    action = "stop"

    def _build_command(self, params: Dict[str, Any]) -> str:
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        return (
            f"! {systemctl} is-active --quiet {service} "
            f"|| {{ {systemctl} stop {service} && echo {CHANGE_MARKER}; }}"
        )


class SystemctlRestartPlugin(_SystemctlServicePlugin):
    """Restart a service and mark the substep as changed."""

    name = "system.service.restart"
    description = "Restart a remote systemd service."
    action = "restart"


class SystemctlDaemonReloadPlugin(BasePlugin):
    """Reload the remote systemd manager configuration."""

    name = "system.systemd.daemon_reload"
    description = "Run systemctl daemon-reload on a remote target."
    optional_params = ("sudo", "user")
    opens_remote_session = True

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message="dry-run: systemctl daemon-reload",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="system.systemd.daemon_reload requires an SSH session")
        systemctl = _systemctl_prefix(params)
        command = f"{systemctl} daemon-reload && echo {CHANGE_MARKER}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="system.systemd.daemon_reload failed",
            data={"action": "daemon-reload"},
        )


class SystemctlReloadPlugin(_SystemctlServicePlugin):
    """Reload a service and mark the substep as changed."""

    name = "system.service.reload"
    description = "Reload a remote systemd service."
    action = "reload"


class SystemctlEnablePlugin(_SystemctlServicePlugin):
    """Enable a service only when it is not already enabled."""

    name = "system.service.enable"
    description = "Enable a remote systemd service."
    action = "enable"

    def _build_command(self, params: Dict[str, Any]) -> str:
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        return (
            f"{systemctl} is-enabled --quiet {service} "
            f"|| {{ {systemctl} enable {service} && echo {CHANGE_MARKER}; }}"
        )


class SystemctlDisablePlugin(_SystemctlServicePlugin):
    """Disable a service only when it is enabled."""

    name = "system.service.disable"
    description = "Disable a remote systemd service."
    action = "disable"

    def _build_command(self, params: Dict[str, Any]) -> str:
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        return (
            f"! {systemctl} is-enabled --quiet {service} "
            f"|| {{ {systemctl} disable {service} && echo {CHANGE_MARKER}; }}"
        )


class SystemctlStatusPlugin(_SystemctlServicePlugin):
    """Return systemctl status output without changing the target."""

    name = "system.service.status"
    description = "Read remote systemd service status."
    action = "status"

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.ssh_client is None:
            return PluginResult.failure(message="system.service.status requires an SSH session")
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        rc, out, err = exec_remote(context, f"{systemctl} status --no-pager {service} || true")
        return PluginResult.success(
            changed=False,
            rc=0,
            stdout=out,
            stderr=err,
            data={"service": params["service"], "raw_rc": rc},
        )


class SystemctlIsActivePlugin(_SystemctlServicePlugin):
    """Check whether a service is active without changing the target."""

    name = "system.service.active_check"
    description = "Check remote systemd active state."
    action = "is-active"
    optional_params = (*_SystemctlServicePlugin.optional_params, "fail_on_inactive")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        rc, out, err = exec_remote(context, f"{systemctl} is-active {service}")
        active = rc == 0 and out.strip() == "active"
        if not active and bool(params.get("fail_on_inactive", False)):
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="service is not active")
        return PluginResult.success(
            changed=False,
            stdout=out,
            stderr=err,
            data={"service": params["service"], "active": active, "state": out.strip()},
        )


class SystemctlIsEnabledPlugin(_SystemctlServicePlugin):
    """Check whether a service is enabled without changing the target."""

    name = "system.service.enabled_check"
    description = "Check remote systemd enabled state."
    action = "is-enabled"
    optional_params = (*_SystemctlServicePlugin.optional_params, "fail_on_disabled")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        rc, out, err = exec_remote(context, f"{systemctl} is-enabled {service}")
        enabled = rc == 0 and out.strip() == "enabled"
        if not enabled and bool(params.get("fail_on_disabled", False)):
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="service is not enabled")
        return PluginResult.success(
            changed=False,
            stdout=out,
            stderr=err,
            data={"service": params["service"], "enabled": enabled, "state": out.strip()},
        )


class SystemctlMaskPlugin(_SystemctlServicePlugin):
    """Mask a service only when it is not already masked."""

    name = "system.service.mask"
    description = "Mask a remote systemd service."
    action = "mask"

    def _build_command(self, params: Dict[str, Any]) -> str:
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        return (
            f"{systemctl} is-enabled {service} 2>/dev/null | grep -qx masked "
            f"|| {{ {systemctl} mask {service} && echo {CHANGE_MARKER}; }}"
        )


class SystemctlUnmaskPlugin(_SystemctlServicePlugin):
    """Unmask a service only when it is currently masked."""

    name = "system.service.unmask"
    description = "Unmask a remote systemd service."
    action = "unmask"

    def _build_command(self, params: Dict[str, Any]) -> str:
        systemctl = _systemctl_prefix(params)
        service = quote(params["service"])
        return (
            f"{systemctl} is-enabled {service} 2>/dev/null | grep -qx masked "
            f"&& {{ {systemctl} unmask {service} && echo {CHANGE_MARKER}; }} || true"
        )
