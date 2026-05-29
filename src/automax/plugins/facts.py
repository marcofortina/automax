# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote Linux facts gathering plugins."""

from __future__ import annotations

import json
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import exec_remote, heredoc_to_stdin, quote, result_from_remote


def _run_json(context: ExecutionContext, command: str, message: str) -> PluginResult:
    rc, out, err = exec_remote(context, command)
    if rc != 0:
        return PluginResult.failure(rc=rc, stdout=out, stderr=err, message=message)
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError as exc:
        return PluginResult.failure(rc=rc, stdout=out, stderr=err, message=f"{message}: invalid JSON: {exc}")
    return PluginResult.success(changed=False, rc=rc, stdout=out, stderr=err, data=data)


class FactsOsPlugin(BasePlugin):
    name = "os.facts"
    description = "Gather remote operating-system, kernel, architecture and hostname facts."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        script = r'''
import json
import platform
import socket
from pathlib import Path

def normalize_arch(machine):
    raw = (machine or '').strip().lower()
    if raw in {'x86_64', 'amd64'}:
        return 'x86_64', 64
    if raw in {'i386', 'i486', 'i586', 'i686', 'x86'}:
        return 'x86', 32
    if raw in {'aarch64', 'arm64'}:
        return 'arm64', 64
    if raw.startswith('armv') or raw in {'arm', 'armhf', 'armel'}:
        return 'arm', 32
    if raw == 'ppc64le':
        return 'ppc64le', 64
    if raw == 's390x':
        return 's390x', 64
    if raw == 'riscv64':
        return 'riscv64', 64
    return 'unknown', 0

facts = {}
path = Path('/etc/os-release')
if path.exists():
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            facts[key.lower()] = value.strip().strip('\"')
uname = platform.uname()
normalized, bits = normalize_arch(uname.machine)
facts['kernel'] = {'name': uname.system, 'release': uname.release, 'version': uname.version, 'machine': uname.machine}
facts['arch'] = {'raw': uname.machine, 'normalized': normalized, 'bits': bits}
facts['hostname'] = socket.gethostname()
print(json.dumps({'os': facts}, sort_keys=True))
'''
        return _run_json(context, heredoc_to_stdin("python3 -", script, prefix="AUTOMAX_PY"), "os.facts failed")


class OsArchCheckPlugin(BasePlugin):
    name = "os.arch.check"
    description = "Assert that the remote normalized architecture matches an allowed value."
    optional_params = ("arch", "any_of", "sudo")
    opens_remote_session = True
    supports_check_mode = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if not (params.get("arch") or params.get("any_of")):
            raise PluginValidationError("os.arch.check requires arch or any_of")

    def _allowed(self, params: Dict[str, Any]) -> list[str]:
        raw = params.get("any_of", params.get("arch"))
        if isinstance(raw, str):
            return [raw]
        return [str(item) for item in raw]

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        allowed = " ".join(quote(item) for item in self._allowed(params))
        script = r'''
raw=$(uname -m | tr '[:upper:]' '[:lower:]')
case "$raw" in
  x86_64|amd64) arch=x86_64 ;;
  i386|i486|i586|i686|x86) arch=x86 ;;
  aarch64|arm64) arch=arm64 ;;
  armv*|arm|armhf|armel) arch=arm ;;
  ppc64le) arch=ppc64le ;;
  s390x) arch=s390x ;;
  riscv64) arch=riscv64 ;;
  *) arch=unknown ;;
esac
for allowed in "$@"; do [ "$arch" = "$allowed" ] && exit 0; done
echo "unsupported architecture: $arch (raw=$raw)" >&2
exit 1
'''
        return [heredoc_to_stdin(f"sh -s -- {allowed}", script, prefix="AUTOMAX_SH")]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="os.arch.check failed", data={"allowed": self._allowed(params)})


class FactsNetworkPlugin(BasePlugin):
    name = "facts.network"
    description = "Gather remote network facts."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        script = r'''
import json
import socket
import subprocess
facts = {'hostname': socket.gethostname(), 'addresses': []}
try:
    raw = subprocess.check_output(['ip', '-j', 'addr'], text=True)
    facts['interfaces'] = json.loads(raw)
except Exception:
    try:
        raw = subprocess.check_output(['hostname', '-I'], text=True)
        facts['addresses'] = [item for item in raw.split() if item]
    except Exception:
        pass
print(json.dumps({'network': facts}, sort_keys=True))
'''
        return _run_json(context, heredoc_to_stdin("python3 -", script, prefix="AUTOMAX_PY"), "facts.network failed")


class FactsPackagesPlugin(BasePlugin):
    name = "os.package.facts"
    description = "Gather remote package facts from dpkg or rpm."
    optional_params = ("manager", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        manager = str(params.get("manager", "auto"))
        script = r'''
import json
import shutil
import subprocess
import sys
manager = sys.argv[1]
packages = []
if manager in ('auto', 'apt', 'dpkg') and shutil.which('dpkg-query'):
    raw = subprocess.check_output(['dpkg-query', '-W', '-f=${Package}\t${Version}\n'], text=True, errors='replace')
    packages = [{'name': line.split('\t', 1)[0], 'version': line.split('\t', 1)[1]} for line in raw.splitlines() if '\t' in line]
    manager = 'dpkg'
elif manager in ('auto', 'rpm', 'dnf', 'yum') and shutil.which('rpm'):
    raw = subprocess.check_output(['rpm', '-qa', '--qf', '%{NAME}\t%{VERSION}-%{RELEASE}\n'], text=True, errors='replace')
    packages = [{'name': line.split('\t', 1)[0], 'version': line.split('\t', 1)[1]} for line in raw.splitlines() if '\t' in line]
    manager = 'rpm'
else:
    raise SystemExit('no supported package database found')
print(json.dumps({'packages': packages, 'manager': manager}, sort_keys=True))
'''
        return _run_json(context, heredoc_to_stdin(f"python3 - {quote(manager)}", script, prefix="AUTOMAX_PY"), "os.package.facts failed")


class FactsServicesPlugin(BasePlugin):
    name = "system.service.facts"
    description = "Gather remote systemd service facts."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        script = r'''
import json
import subprocess
services = []
raw = subprocess.check_output(['systemctl', 'list-units', '--type=service', '--all', '--no-legend', '--no-pager'], text=True, errors='replace')
for line in raw.splitlines():
    parts = line.split(None, 4)
    if len(parts) >= 4:
        services.append({'unit': parts[0], 'load': parts[1], 'active': parts[2], 'sub': parts[3], 'description': parts[4] if len(parts) > 4 else ''})
print(json.dumps({'services': services}, sort_keys=True))
'''
        return _run_json(context, heredoc_to_stdin("python3 -", script, prefix="AUTOMAX_PY"), "system.service.facts failed")


class FactsGatherPlugin(BasePlugin):
    name = "facts.gather"
    description = "Gather selected remote Linux facts."
    optional_params = ("subset", "manager", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        subset = params.get("subset", ["os", "network"])
        if isinstance(subset, str):
            subset = [item.strip() for item in subset.split(",") if item.strip()]
        if not isinstance(subset, list):
            raise PluginValidationError("facts.gather subset must be a list or comma-separated string")
        data: dict[str, Any] = {}
        for item in subset:
            plugin = {
                "os": FactsOsPlugin(),
                "network": FactsNetworkPlugin(),
                "packages": FactsPackagesPlugin(),
                "services": FactsServicesPlugin(),
            }.get(str(item))
            if plugin is None:
                raise PluginValidationError("facts.gather subset entries must be os, network, packages or services")
            result = plugin.execute(params, context)
            if not result.ok:
                return result
            data.update(result.data or {})
        return PluginResult.success(changed=False, data=data, stdout=json.dumps(data, sort_keys=True))
