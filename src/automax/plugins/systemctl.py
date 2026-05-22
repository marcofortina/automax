"""
Remote systemctl macro plugins.
"""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import CHANGE_MARKER, exec_remote, quote, result_from_remote


def _systemctl_prefix(params: Dict[str, Any]) -> str:
    prefix = "systemctl --user" if bool(params.get("user", False)) else "systemctl"
    if bool(params.get("sudo", False)):
        return f"sudo -n {prefix}"
    return prefix


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

    name = "systemctl.start"
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

    name = "systemctl.stop"
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

    name = "systemctl.restart"
    description = "Restart a remote systemd service."
    action = "restart"


class SystemctlDaemonReloadPlugin(BasePlugin):
    """Reload the remote systemd manager configuration."""

    name = "systemctl.daemon_reload"
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
            return PluginResult.failure(message="systemctl.daemon_reload requires an SSH session")
        systemctl = _systemctl_prefix(params)
        command = f"{systemctl} daemon-reload && echo {CHANGE_MARKER}"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="systemctl.daemon_reload failed",
            data={"action": "daemon-reload"},
        )
