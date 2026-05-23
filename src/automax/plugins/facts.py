# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote Linux facts gathering plugins."""

from __future__ import annotations

import json
from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import exec_remote, quote


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
    name = "facts.os"
    description = "Gather remote operating-system facts."
    optional_params = ("sudo",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        script = r'''
import json
from pathlib import Path
facts = {}
path = Path('/etc/os-release')
if path.exists():
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            facts[key.lower()] = value.strip().strip('"')
print(json.dumps({'os': facts}, sort_keys=True))
'''
        return _run_json(context, f"python3 - <<'PY'\n{script}\nPY", "facts.os failed")


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
        return _run_json(context, f"python3 - <<'PY'\n{script}\nPY", "facts.network failed")


class FactsPackagesPlugin(BasePlugin):
    name = "facts.packages"
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
        return _run_json(context, f"python3 - {quote(manager)} <<'PY'\n{script}\nPY", "facts.packages failed")


class FactsServicesPlugin(BasePlugin):
    name = "facts.services"
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
        return _run_json(context, f"python3 - <<'PY'\n{script}\nPY", "facts.services failed")


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
