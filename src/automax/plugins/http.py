# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
HTTP/API plugins executed from the controller.
"""

from __future__ import annotations

import json as jsonlib
import ssl
import time
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import quote


def _headers(params: Dict[str, Any]) -> Dict[str, str]:
    raw = params.get("headers", {}) or {}
    if not isinstance(raw, dict):
        raise PluginValidationError("http headers must be a mapping")
    return {str(key): str(value) for key, value in raw.items()}


def _body(params: Dict[str, Any], headers: Dict[str, str]) -> bytes | None:
    if "json" in params:
        headers.setdefault("Content-Type", "application/json")
        return jsonlib.dumps(params["json"]).encode("utf-8")
    if "body" not in params or params.get("body") is None:
        return None
    body = params["body"]
    if isinstance(body, bytes):
        return body
    return str(body).encode(str(params.get("encoding", "utf-8")))


def _ssl_context(params: Dict[str, Any]):
    if bool(params.get("validate_tls", True)):
        return None
    return ssl._create_unverified_context()  # noqa: S323 - explicit lab/operator override.


def _perform(params: Dict[str, Any]) -> Dict[str, Any]:
    headers = _headers(params)
    data = _body(params, headers)
    method = str(params.get("method", "GET" if data is None else "POST")).upper()
    request = Request(str(params["url"]), data=data, headers=headers, method=method)
    timeout = float(params.get("timeout", 30))
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context(params)) as response:
            response_body = response.read().decode(str(params.get("encoding", "utf-8")), errors="replace")
            return {
                "status": int(response.status),
                "headers": dict(response.headers.items()),
                "body": response_body,
                "error": "",
            }
    except HTTPError as exc:
        response_body = exc.read().decode(str(params.get("encoding", "utf-8")), errors="replace")
        return {
            "status": int(exc.code),
            "headers": dict(exc.headers.items()) if exc.headers else {},
            "body": response_body,
            "error": str(exc),
        }
    except URLError as exc:
        raise PluginValidationError(f"HTTP request failed: {exc}") from exc


def _expected_statuses(params: Dict[str, Any], default: int = 200) -> set[int]:
    raw = params.get("status", params.get("expected_status", default))
    values = raw if isinstance(raw, list) else [raw]
    return {int(value) for value in values}


def _check_response(params: Dict[str, Any], response: Dict[str, Any]) -> PluginResult:
    expected = _expected_statuses(params)
    status = int(response["status"])
    status_matches = status in expected
    contains = params.get("contains")
    body_matches = contains is None or str(contains) in response["body"]
    data = dict(response)
    data.update(
        {
            "expected_status": sorted(expected),
            "status_matches": status_matches,
            "body_matches": body_matches,
            "matches": status_matches and body_matches,
        }
    )
    return PluginResult.success(changed=False, stdout=response["body"], data=data)


def _assert_response(params: Dict[str, Any], response: Dict[str, Any]) -> PluginResult:
    checked = _check_response(params, response)
    if checked.data["matches"]:
        return checked
    if not checked.data["status_matches"]:
        return PluginResult.failure(
            rc=1,
            stdout=response["body"],
            message=f"unexpected HTTP status {response['status']}, expected {checked.data['expected_status']}",
            data=checked.data,
        )
    return PluginResult.failure(
        rc=1,
        stdout=response["body"],
        message="HTTP response body does not contain expected text",
        data=checked.data,
    )


class HttpRequestPlugin(BasePlugin):
    """Perform an HTTP request from the controller."""

    name = "network.http.request"
    description = "Perform an HTTP request from the controller."
    required_params = ("url",)
    optional_params = (
        "method",
        "headers",
        "body",
        "json",
        "timeout",
        "encoding",
        "validate_tls",
        "expected_status",
        "status",
    )
    opens_remote_session = False

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        method = str(params.get("method", "GET" if "body" not in params and "json" not in params else "POST")).upper()
        command = ["curl", "-i", "-X", quote(method)]
        for key, value in _headers(params).items():
            command.extend(["-H", quote(f"{key}: {value}")])
        if "json" in params:
            command.extend(["-H", quote("Content-Type: application/json"), "--data", quote(jsonlib.dumps(params["json"]))])
        elif params.get("body") is not None:
            command.extend(["--data", quote(params["body"])])
        command.append(quote(params["url"]))
        return [" ".join(command)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        response = _perform(params)
        if "expected_status" in params or "status" in params:
            return _assert_response(params, response)
        return PluginResult.success(changed=False, stdout=response["body"], data=response)


class HttpAssertPlugin(HttpRequestPlugin):
    """Assert HTTP status/body from the controller."""

    name = "network.http.check"
    description = "Check HTTP status and optional body content."
    optional_params = (*HttpRequestPlugin.optional_params, "contains")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        return _check_response(params, _perform(params))


class HttpWaitPlugin(HttpAssertPlugin):
    """Wait until an HTTP endpoint matches expected status/body."""

    name = "network.http.wait"
    description = "Wait until an HTTP endpoint matches expected status and optional body content."
    optional_params = (*HttpAssertPlugin.optional_params, "interval")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        timeout = float(params.get("timeout", 60))
        interval = float(params.get("interval", 2))
        deadline = time.monotonic() + timeout
        last_result: PluginResult | None = None
        while True:
            try:
                last_result = _check_response(params, _perform(params))
                if last_result.data["matches"]:
                    return last_result
            except PluginValidationError as exc:
                last_result = PluginResult.failure(message=str(exc))
            if time.monotonic() >= deadline:
                return PluginResult.failure(
                    message="network.http.wait timed out",
                    stdout=last_result.stdout if last_result else "",
                    data=last_result.data if last_result else {},
                )
            time.sleep(interval)
