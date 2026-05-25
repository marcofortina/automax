# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Remote operating-system detection helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetOS:
    """Normalized OS facts used by capability and plugin preflight."""

    id: str = "unknown"
    id_like: tuple[str, ...] = ()
    name: str = ""
    pretty_name: str = ""
    version: str = ""
    version_id: str = ""
    version_codename: str = ""
    family: str = "unknown"
    package_manager: str = "unknown"

    @property
    def is_debian_like(self) -> bool:
        return self.family == "debian"

    @property
    def is_rhel_like(self) -> bool:
        return self.family == "rhel"


def parse_os_release(text: str) -> TargetOS:
    """Parse /etc/os-release content into a normalized target OS."""
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"').strip("'")
    os_id = values.get("ID", "unknown").lower()
    id_like = tuple(item.lower() for item in values.get("ID_LIKE", "").split() if item)
    family = "unknown"
    package_manager = "unknown"
    debian_markers = {"debian", "ubuntu", "linuxmint", "pop", "raspbian"}
    rhel_markers = {"rhel", "fedora", "centos", "rocky", "almalinux", "ol", "oracle", "amzn"}
    candidates = {os_id, *id_like}
    if candidates & debian_markers:
        family = "debian"
        package_manager = "apt"
    elif candidates & rhel_markers:
        family = "rhel"
        package_manager = "dnf"
    return TargetOS(
        id=os_id,
        id_like=id_like,
        name=values.get("NAME", ""),
        pretty_name=values.get("PRETTY_NAME", ""),
        version=values.get("VERSION", ""),
        version_id=values.get("VERSION_ID", ""),
        version_codename=values.get("VERSION_CODENAME", values.get("UBUNTU_CODENAME", "")),
        family=family,
        package_manager=package_manager,
    )


DETECT_OS_COMMAND = "cat /etc/os-release 2>/dev/null || true"
