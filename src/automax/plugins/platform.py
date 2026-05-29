# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Platform/backend detection plugins for portable Linux operations."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin
from automax.plugins.remote_utils import exec_remote, heredoc_to_stdin, sudo_prefix



class PlatformFactsPlugin(BasePlugin):
    name = "os.platform.facts"
    description = "Collect portable Linux backend facts for package, service, network, resolver and trust-store operations."
    required_params: tuple[str, ...] = ()
    optional_params = ("sudo",)
    opens_remote_session = True
    supports_check_mode = True

    def diff_preview_reason(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return "os.platform.facts is a read-only backend detection plugin and does not change files"

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        sudo = sudo_prefix(params, default=False)
        script = r'''
set -eu
has() { command -v "$1" >/dev/null 2>&1; }
first_of() { for item in "$@"; do if has "$item"; then printf '%s' "$item"; return 0; fi; done; printf 'unknown'; }
package_manager=$(first_of apt-get dnf yum zypper pacman)
service_manager=unknown
if has systemctl; then service_manager=systemd; elif has service; then service_manager=sysvinit; fi
network_backend=runtime
if has nmcli; then network_backend=networkmanager; elif [ -d /etc/systemd/network ]; then network_backend=systemd-networkd; elif [ -d /etc/sysconfig/network-scripts ]; then network_backend=ifcfg; elif [ -e /etc/network/interfaces ]; then network_backend=ifupdown; fi
resolver_backend=plain-file
if [ -L /etc/resolv.conf ]; then
  target=$(readlink -f /etc/resolv.conf || true)
  case "$target" in
    *systemd/resolve*) resolver_backend=systemd-resolved ;;
    *NetworkManager*) resolver_backend=networkmanager ;;
    *) resolver_backend=symlink ;;
  esac
elif [ -e /run/systemd/resolve/resolv.conf ]; then resolver_backend=systemd-resolved
elif [ -d /etc/resolvconf ]; then resolver_backend=resolvconf
fi
trust_store=unknown
if has update-ca-certificates; then trust_store=debian-ca-certificates; elif has update-ca-trust; then trust_store=redhat-ca-trust; fi
printf 'package_manager=%s\nservice_manager=%s\nnetwork_backend=%s\nresolver_backend=%s\ntrust_store=%s\n' "$package_manager" "$service_manager" "$network_backend" "$resolver_backend" "$trust_store"
'''
        return [heredoc_to_stdin(f"{sudo}sh -s", script, prefix="AUTOMAX_SH")]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="os.platform.facts failed")
        data = {}
        for line in out.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key] = value
        return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data=data)
