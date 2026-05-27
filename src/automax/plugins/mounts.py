# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Linux mount and fstab management plugins."""

from __future__ import annotations

from typing import Any, Dict

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import exec_remote, quote, result_from_remote, sudo_prefix



def _fstab_line(params: Dict[str, Any]) -> str:
    return " ".join(
        [
            str(params["src"]),
            str(params["path"]),
            str(params["fstype"]),
            str(params.get("opts", "defaults")),
            str(params.get("dump", 0)),
            str(params.get("passno", 0)),
        ]
    )


class FstabEntryPlugin(BasePlugin):
    name = "fstab.entry"
    description = "Ensure an /etc/fstab entry is present or absent."
    required_params = ("src", "path", "fstype")
    optional_params = ("opts", "dump", "passno", "state", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        if str(params.get("state", "present")) not in {"present", "absent"}:
            raise PluginValidationError("fstab.entry state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        state = str(params.get("state", "present"))
        line = _fstab_line(params)
        script = r'''
set -eu
line=$1
mountpoint=$2
state=$3
file=/etc/fstab
touch "$file"
tmp=$(mktemp)
awk -v mp="$mountpoint" '$2 != mp {print}' "$file" > "$tmp"
if [ "$state" = present ]; then
  printf '%s\n' "$line" >> "$tmp"
fi
if cmp -s "$tmp" "$file"; then
  rm -f "$tmp"
else
  cat "$tmp" > "$file"
  rm -f "$tmp"
  echo __AUTOMAX_CHANGED__
fi
'''
        command = f"{sudo_prefix(params, default=True)}sh -s -- {quote(line)} {quote(params['path'])} {quote(state)} <<'SH'\n{script}\nSH"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="fstab.entry failed", data={"line": line})


class MountPresentPlugin(BasePlugin):
    name = "mount.present"
    description = "Ensure a filesystem is mounted and optionally persisted in fstab."
    required_params = ("src", "path", "fstype")
    optional_params = ("opts", "persist", "dump", "passno", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        line = _fstab_line(params)
        persist = bool(params.get("persist", False))
        script = r'''
set -eu
src=$1
path=$2
fstype=$3
opts=$4
persist=$5
line=$6
changed=0
mkdir -p "$path"
if ! findmnt -rn "$path" >/dev/null 2>&1; then
  mount -t "$fstype" -o "$opts" "$src" "$path"
  changed=1
fi
if [ "$persist" = true ]; then
  tmp=$(mktemp)
  awk -v mp="$path" '$2 != mp {print}' /etc/fstab > "$tmp"
  printf '%s\n' "$line" >> "$tmp"
  if ! cmp -s "$tmp" /etc/fstab; then
    cat "$tmp" > /etc/fstab
    changed=1
  fi
  rm -f "$tmp"
fi
if [ "$changed" = 1 ]; then echo __AUTOMAX_CHANGED__; fi
'''
        command = f"{sudo_prefix(params, default=True)}sh -s -- {quote(params['src'])} {quote(params['path'])} {quote(params['fstype'])} {quote(params.get('opts','defaults'))} {quote(str(persist).lower())} {quote(line)} <<'SH'\n{script}\nSH"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="mount.present failed")


class MountAbsentPlugin(BasePlugin):
    name = "mount.absent"
    description = "Ensure a mount point is unmounted and optionally removed from fstab."
    required_params = ("path",)
    optional_params = ("persist", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        persist = bool(params.get("persist", False))
        script = r'''
set -eu
path=$1
persist=$2
changed=0
if findmnt -rn "$path" >/dev/null 2>&1; then
  umount "$path"
  changed=1
fi
if [ "$persist" = true ] && [ -e /etc/fstab ]; then
  tmp=$(mktemp)
  awk -v mp="$path" '$2 != mp {print}' /etc/fstab > "$tmp"
  if ! cmp -s "$tmp" /etc/fstab; then
    cat "$tmp" > /etc/fstab
    changed=1
  fi
  rm -f "$tmp"
fi
if [ "$changed" = 1 ]; then echo __AUTOMAX_CHANGED__; fi
'''
        command = f"{sudo_prefix(params, default=True)}sh -s -- {quote(params['path'])} {quote(str(persist).lower())} <<'SH'\n{script}\nSH"
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="mount.absent failed")
