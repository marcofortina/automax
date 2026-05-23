# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Exportable JSON schemas for Automax operator-owned YAML files.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

SCHEMA_VERSION = "https://json-schema.org/draft/2020-12/schema"
AUTOMAX_SCHEMA_ID = "https://marcofortina.github.io/automax/schemas"


def export_schema(kind: str = "job") -> Dict[str, Any]:
    """Return an exportable JSON Schema document for one Automax YAML kind."""
    normalized = str(kind or "job").strip().lower()
    schemas = _schemas()
    if normalized == "all":
        return {
            "$schema": SCHEMA_VERSION,
            "$id": f"{AUTOMAX_SCHEMA_ID}/all.schema.json",
            "title": "Automax schemas",
            "type": "object",
            "additionalProperties": False,
            "properties": {name: deepcopy(schema) for name, schema in schemas.items()},
            "required": sorted(schemas),
        }
    if normalized not in schemas:
        supported = ", ".join([*sorted(schemas), "all"])
        raise ValueError(f"unsupported schema kind: {kind}. Supported kinds: {supported}")
    return deepcopy(schemas[normalized])


def _schemas() -> Dict[str, Dict[str, Any]]:
    return {
        "job": _job_schema(),
        "inventory": _inventory_schema(),
        "vars": _vars_schema(),
        "secrets": _secrets_schema(),
    }


def _metadata_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
        },
    }


def _tags_schema() -> Dict[str, Any]:
    return {
        "oneOf": [
            {"type": "string", "minLength": 1},
            {"type": "array", "items": {"type": "string", "minLength": 1}},
        ]
    }


def _strategy_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "mode": {"type": "string", "enum": ["serial", "parallel", "rolling"]},
            "max_parallel": {"type": "integer", "minimum": 1},
            "batch_size": {"type": "integer", "minimum": 1},
            "pause_between_batches": {"type": ["integer", "number"], "minimum": 0},
        },
    }


def _failure_policy_schema() -> Dict[str, Any]:
    action = {"type": "string", "enum": ["stop_job", "stop_task", "stop_host", "continue"]}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "onFailure": action,
            "onUnreachable": action,
            "maxFailedHosts": {"type": "integer", "minimum": 1},
        },
    }


def _timeouts_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "connect": {"type": ["integer", "number"], "minimum": 0},
            "command": {"type": ["integer", "number"], "minimum": 0},
        },
    }


def _error_policy_schema() -> Dict[str, Any]:
    rule = {
        "oneOf": [
            {"type": "string", "minLength": 1},
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["pattern"],
                "properties": {
                    "stream": {
                        "type": "string",
                        "enum": ["stdout", "stderr", "combined", "message"],
                    },
                    "pattern": {"type": "string", "minLength": 1},
                    "reason": {"type": "string"},
                },
            },
        ]
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "acceptedRc": {
                "type": "array",
                "items": {"type": "integer"},
                "uniqueItems": True,
            },
            "expected": {"type": "array", "items": rule},
            "fail": {"type": "array", "items": rule},
            "unmatched": {"type": "string", "enum": ["fail", "warn", "ignore"]},
            "acceptedStatus": {"type": "string", "enum": ["warning", "success"]},
        },
    }


def _substep_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["id"],
        "oneOf": [
            {"required": ["use"]},
            {"required": ["plugin"]},
        ],
        "properties": {
            "id": {"type": "string", "pattern": "^[A-Za-z0-9_.-]+$"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "targets": {"type": ["string", "array"], "items": {"type": "string"}},
            "tags": _tags_schema(),
            "timeouts": _timeouts_schema(),
            "errorPolicy": _error_policy_schema(),
            "when": {},
            "use": {"type": "string", "minLength": 1},
            "plugin": {"type": "string", "minLength": 1},
            "with": {"type": "object", "additionalProperties": True},
            "params": {"type": "object", "additionalProperties": True},
            "register": {"type": "object", "additionalProperties": {"type": "string"}},
            "artifacts": {"type": "object", "additionalProperties": {"type": "string"}},
            "artifact": {"type": "object", "additionalProperties": {"type": "string"}},
        },
    }


def _step_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "substeps"],
        "properties": {
            "id": {"type": "string", "pattern": "^[A-Za-z0-9_.-]+$"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "vars": {"type": "object", "additionalProperties": True},
            "targets": {"type": ["string", "array"], "items": {"type": "string"}},
            "strategy": _strategy_schema(),
            "failurePolicy": _failure_policy_schema(),
            "errorPolicy": _error_policy_schema(),
            "timeouts": _timeouts_schema(),
            "tags": _tags_schema(),
            "substeps": {"type": "array", "minItems": 1, "items": _substep_schema()},
        },
    }


def _task_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "steps"],
        "properties": {
            "id": {"type": "string", "pattern": "^[A-Za-z0-9_.-]+$"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "vars": {"type": "object", "additionalProperties": True},
            "targets": {"type": ["string", "array"], "items": {"type": "string"}},
            "strategy": _strategy_schema(),
            "failurePolicy": _failure_policy_schema(),
            "errorPolicy": _error_policy_schema(),
            "timeouts": _timeouts_schema(),
            "tags": _tags_schema(),
            "steps": {"type": "array", "minItems": 1, "items": _step_schema()},
        },
    }


def _job_schema() -> Dict[str, Any]:
    return {
        "$schema": SCHEMA_VERSION,
        "$id": f"{AUTOMAX_SCHEMA_ID}/job.schema.json",
        "title": "Automax Job",
        "description": "Canonical Automax YAML job definition.",
        "type": "object",
        "additionalProperties": False,
        "required": ["apiVersion", "kind", "tasks"],
        "properties": {
            "apiVersion": {"const": "automax.io/v1"},
            "kind": {"const": "Job"},
            "metadata": _metadata_schema(),
            "vars": {"type": "object", "additionalProperties": True},
            "targets": {"type": ["string", "array"], "items": {"type": "string"}},
            "strategy": _strategy_schema(),
            "failurePolicy": _failure_policy_schema(),
            "errorPolicy": _error_policy_schema(),
            "timeouts": _timeouts_schema(),
            "tags": _tags_schema(),
            "tasks": {"type": "array", "minItems": 1, "items": _task_schema()},
        },
    }


def _inventory_schema() -> Dict[str, Any]:
    server_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["host"],
        "properties": {
            "host": {"type": "string", "minLength": 1},
            "hostname": {"type": "string", "minLength": 1},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "user": {"type": "string"},
            "username": {"type": "string"},
            "password": {"type": "string"},
            "key_file": {"type": "string"},
            "key_content": {"type": "string"},
            "groups": {"type": "array", "items": {"type": "string"}},
            "vars": {"type": "object", "additionalProperties": True},
            "ssh": {"type": "object", "additionalProperties": True},
            "timeouts": _timeouts_schema(),
        },
    }
    static_inventory = {
        "type": "object",
        "additionalProperties": False,
        "required": ["servers"],
        "properties": {
            "servers": {
                "oneOf": [
                    {
                        "type": "object",
                        "minProperties": 1,
                        "additionalProperties": server_schema,
                    },
                    {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "allOf": [
                                server_schema,
                                {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {"name": {"type": "string", "minLength": 1}},
                                },
                            ]
                        },
                    },
                ]
            },
            "groups": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
            },
        },
    }
    provider = _inventory_provider_schema()
    return {
        "$schema": SCHEMA_VERSION,
        "$id": f"{AUTOMAX_SCHEMA_ID}/inventory.schema.json",
        "title": "Automax Inventory",
        "description": "Static or dynamic Automax inventory file.",
        "oneOf": [
            static_inventory,
            provider,
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["inventory"],
                "properties": {"inventory": provider},
            },
        ],
    }


def _inventory_provider_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["provider"],
        "properties": {
            "provider": {"type": "string", "enum": ["file", "command", "http"]},
            "path": {"type": "string", "minLength": 1},
            "command": {
                "oneOf": [
                    {"type": "string", "minLength": 1},
                    {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                ]
            },
            "url": {"type": "string", "minLength": 1},
            "method": {"type": "string", "enum": ["GET"]},
            "headers": {"type": "object", "additionalProperties": {"type": "string"}},
            "format": {"type": "string", "enum": ["auto", "yaml", "json"]},
            "timeout": {"type": "integer", "minimum": 1},
            "cwd": {"type": "string"},
            "env": {"type": "object", "additionalProperties": True},
            "shell": {"type": "boolean"},
            "encoding": {"type": "string"},
        },
    }


def _vars_schema() -> Dict[str, Any]:
    return {
        "$schema": SCHEMA_VERSION,
        "$id": f"{AUTOMAX_SCHEMA_ID}/vars.schema.json",
        "title": "Automax Variables",
        "description": "External Automax variables file.",
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "vars": {"type": "object", "additionalProperties": True},
        },
    }


def _secrets_schema() -> Dict[str, Any]:
    provider = {
        "type": "object",
        "additionalProperties": False,
        "required": ["provider"],
        "properties": {
            "provider": {"type": "string", "enum": ["env", "file", "command"]},
            "name": {"type": "string"},
            "var": {"type": "string"},
            "path": {"type": "string"},
            "command": {
                "oneOf": [
                    {"type": "string", "minLength": 1},
                    {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                ]
            },
            "timeout": {"type": "integer", "minimum": 1},
            "cwd": {"type": "string"},
            "env": {"type": "object", "additionalProperties": True},
            "shell": {"type": "boolean"},
            "strip": {"type": "boolean"},
        },
    }
    return {
        "$schema": SCHEMA_VERSION,
        "$id": f"{AUTOMAX_SCHEMA_ID}/secrets.schema.json",
        "title": "Automax Secrets",
        "description": "External Automax env, file and command secrets file.",
        "type": "object",
        "additionalProperties": False,
        "required": ["secrets"],
        "properties": {
            "secrets": {
                "type": "object",
                "additionalProperties": {
                    "oneOf": [
                        {"type": "string"},
                        provider,
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "env": {"type": "string"},
                                "file": {"type": "string"},
                                "command": provider["properties"]["command"],
                            },
                        },
                    ]
                },
            }
        },
    }
