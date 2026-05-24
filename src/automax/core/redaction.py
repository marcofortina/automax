# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Secret redaction policy helpers."""

from __future__ import annotations

import re
from typing import Any, Iterable

SENSITIVE_KEY_RE = re.compile(r"(?i)(password|passwd|passphrase|token|secret|api[_-]?key|private[_-]?key|credential|totp|otp)")
SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(password|passwd|passphrase|token|secret|api[_-]?key|private[_-]?key|credential|totp|otp)\b\s*[:=]\s*([^\s,'\"]+)"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.DOTALL)
BEARER_RE = re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9._~+/=-]{8,}")


def iter_secret_texts(value: Any) -> Iterable[str]:
    """Yield printable secret values from nested structures."""
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str) and SENSITIVE_KEY_RE.search(str(key)) and len(item) >= 1:
                yield item
            yield from iter_secret_texts(item)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from iter_secret_texts(item)
        return
    if value is None:
        return
    secret_text = str(value)
    if len(secret_text) >= 4:
        yield secret_text


def redact_text(value: str, secrets: dict[str, Any] | None = None, *, extra_values: Iterable[str] = ()) -> str:
    """Redact known secrets plus common secret-shaped assignments from text."""
    masked = str(value)
    for secret in list(iter_secret_texts(secrets or {})) + [str(item) for item in extra_values if str(item)]:
        masked = masked.replace(secret, "***")
    masked = PRIVATE_KEY_RE.sub("***PRIVATE KEY***", masked)
    masked = BEARER_RE.sub(r"\1***", masked)
    masked = SENSITIVE_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=***", masked)
    return masked


def redact_mapping(value: Any, secrets: dict[str, Any] | None = None) -> Any:
    """Redact strings in nested mappings and mask sensitive keys entirely."""
    if isinstance(value, dict):
        return {
            key: "***" if SENSITIVE_KEY_RE.search(str(key)) else redact_mapping(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_mapping(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_mapping(item, secrets) for item in value)
    if isinstance(value, str):
        return redact_text(value, secrets)
    return value


def find_unredacted_secrets(value: Any, secrets: dict[str, Any] | None = None) -> list[str]:
    """Return secret values still visible in a payload."""
    text = value if isinstance(value, str) else repr(value)
    leaked = []
    for secret in iter_secret_texts(secrets or {}):
        if secret and secret in text:
            leaked.append(secret)
    return sorted(set(leaked))
