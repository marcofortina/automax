# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Builtin plugin metadata catalogue.

Runtime plugins intentionally keep their execution logic small. This module owns
user-facing metadata used by ``automax plugins describe`` and generated docs so
that every builtin plugin exposes a complete, deterministic contract.
"""

from __future__ import annotations

from typing import Any

from automax.plugins.base import BasePlugin

PARAMETERS: dict[str, dict[str, Any]] = {
    "allow_replace_non_symlink": {"type": "boolean", "default": False, "description": "Allow force replacement when the destination exists and is not a symlink."},
    "append": {"type": "boolean", "default": False, "description": "Append supplementary groups instead of replacing the user group list."},
    "archive": {"type": "path", "description": "Remote archive path to extract."},
    "body": {"type": "string", "description": "Raw HTTP request body."},
    "command": {"type": "string", "description": "Command line to execute."},
    "comment": {"type": "string", "description": "User account comment or GECOS field."},
    "commit": {"type": "boolean", "default": True, "description": "Commit the database transaction on success; false rolls it back."},
    "compression": {"type": "string", "default": "auto", "description": "Archive compression: auto, none, gzip, bzip2 or xz."},
    "connect_timeout": {"type": "number", "default": 3, "description": "Per-attempt TCP connect timeout in seconds."},
    "connection": {"type": "mapping", "description": "Database connection mapping; values may be rendered from vars or secrets."},
    "contains": {"type": "string", "description": "Required substring in stdout or HTTP response body."},
    "content": {"type": "string", "description": "Text content to write."},
    "count": {"type": "integer", "default": 0, "description": "Maximum regex replacements; 0 means replace all matches."},
    "create": {"type": "boolean", "default": False, "description": "Create the remote file when ensuring a line is present."},
    "create_home": {"type": "boolean", "description": "Create the user's home directory when supported by useradd."},
    "creates": {"type": "path", "description": "Remote path that makes the operation idempotent when already present."},
    "cwd": {"type": "path", "description": "Remote or local working directory for this operation."},
    "dest": {"type": "path", "description": "Destination path."},
    "encoding": {"type": "string", "default": "utf-8", "description": "Text encoding used for command output, HTTP bodies or file content."},
    "env": {"type": "mapping", "description": "Environment variables for a local command."},
    "equals": {"type": "string", "description": "Expected stdout value after trimming whitespace."},
    "excludes": {"type": "list", "description": "Glob patterns excluded from archive creation."},
    "expected_status": {"type": "integer", "default": 200, "description": "Expected HTTP status code."},
    "fail_on_disabled": {"type": "boolean", "default": False, "description": "Fail when the queried service is not enabled."},
    "fail_on_inactive": {"type": "boolean", "default": False, "description": "Fail when the queried service is not active."},
    "fetch": {"type": "string", "default": "all", "description": "Database fetch mode: all, one or none."},
    "force": {"type": "boolean", "default": False, "description": "Force the operation when supported."},
    "get_pty": {"type": "boolean", "default": False, "description": "Request a pseudo-terminal for the remote command."},
    "gid": {"type": "integer", "description": "Numeric group id."},
    "group": {"type": "string", "description": "Primary group, file group owner or remote group name."},
    "groups": {"type": "list", "description": "Supplementary group names."},
    "headers": {"type": "mapping", "description": "HTTP request headers."},
    "home": {"type": "path", "description": "User home directory."},
    "host": {"type": "string", "description": "Hostname or IP address to check from the controller."},
    "ignore_missing": {"type": "boolean", "default": True, "description": "Treat missing processes as success."},
    "interval": {"type": "number", "default": 2, "description": "Polling interval in seconds."},
    "json": {"type": "mapping", "description": "JSON HTTP request body."},
    "key": {"type": "string", "description": "SSH public key line."},
    "password": {"type": "string", "description": "Plaintext password; prefer password_hash when possible."},
    "password_hash": {"type": "string", "description": "crypt(3) password hash passed to usermod --password."},
    "validate": {"type": "boolean", "default": True, "description": "Validate generated or uploaded content before installing it."},
    "line": {"type": "string", "description": "Exact line to ensure in a remote file."},
    "lock": {"type": "boolean", "default": False, "description": "Lock the remote user account."},
    "manager": {"type": "string", "default": "auto", "description": "Package manager: auto, apt, dnf, yum, zypper or pacman."},
    "max_depth": {"type": "integer", "description": "Maximum remote find traversal depth."},
    "method": {"type": "string", "default": "GET", "description": "HTTP request method."},
    "min_free_mb": {"type": "integer", "description": "Minimum free disk space in MiB."},
    "min_free_percent": {"type": "number", "description": "Minimum free disk percentage."},
    "missing_ok": {"type": "boolean", "default": False, "description": "Return success with exists=false when the path is missing."},
    "mode": {"type": "string", "description": "POSIX file mode, for example 0644 or 0755."},
    "name": {"type": "string", "description": "Package, user or group name."},
    "not_contains": {"type": "string", "description": "Substring that must not appear in stdout."},
    "output": {"type": "string", "default": "rows", "description": "Database output format: rows, scalar, json or none."},
    "overwrite": {"type": "boolean", "default": False, "description": "Replace an existing destination when supported."},
    "owner": {"type": "string", "description": "Remote file owner."},
    "packages": {"type": "list", "description": "Package names for package-manager operations."},
    "path": {"type": "path", "description": "Remote or local path, depending on the plugin."},
    "pattern": {"type": "string", "description": "Regex, process pattern or search pattern."},
    "patterns": {"type": "list", "description": "Find-name patterns to match."},
    "pid": {"type": "integer", "description": "Process id."},
    "port": {"type": "integer", "description": "TCP port number."},
    "preserve": {"type": "boolean", "default": False, "description": "Preserve mode, ownership and timestamps when copying."},
    "pty": {"type": "boolean", "default": False, "description": "Request a pseudo-terminal for remote.command."},
    "query": {"type": "string", "description": "SQL query to execute."},
    "query_params": {"type": "sequence", "description": "SQL bind parameters passed to the database driver."},
    "rc": {"type": "integer", "default": 0, "description": "Expected process return code."},
    "recursive": {"type": "boolean", "default": False, "description": "Recurse into directories."},
    "remove_home": {"type": "boolean", "default": False, "description": "Remove the user's home directory when deleting an account."},
    "replacement": {"type": "string", "description": "Regex replacement text."},
    "service": {"type": "string", "description": "systemd service unit name."},
    "shell": {"type": "boolean", "description": "Run a local command through the platform shell."},
    "signal": {"type": "string", "default": "TERM", "description": "Signal name or number sent to a process."},
    "source": {"type": "path", "description": "Remote source path to archive."},
    "src": {"type": "path", "description": "Source path."},
    "state": {"type": "string", "description": "Desired state such as present, absent, started or stopped."},
    "statements": {"type": "list", "description": "SQL statements executed in order inside one transaction."},
    "status": {"type": "integer", "description": "Expected HTTP status code alias."},
    "stdin": {"type": "string", "description": "Text written to remote command standard input."},
    "strip_components": {"type": "integer", "default": 0, "description": "Path components stripped while extracting a tar archive."},
    "success_rc": {"type": "integer", "default": 0, "description": "Return code considered successful."},
    "sudo": {"type": "boolean", "default": False, "description": "Run the remote operation through sudo -n when supported."},
    "system": {"type": "boolean", "default": False, "description": "Create a system user or group."},
    "timeout": {"type": "number", "description": "Operation timeout in seconds."},
    "type": {"type": "string", "description": "Path type filter: path, file, directory, dir, symlink or any."},
    "uid": {"type": "integer", "description": "Numeric user id."},
    "unlock": {"type": "boolean", "default": False, "description": "Unlock the remote user account."},
    "url": {"type": "string", "description": "HTTP URL."},
    "user": {"type": "boolean", "default": False, "description": "Use systemctl --user instead of the system manager."},
    "validate_tls": {"type": "boolean", "default": True, "description": "Validate TLS certificates for HTTPS requests."},
    "values": {"type": "mapping", "description": "Additional template values exposed as values.*."},
    "changed": {"type": "boolean", "default": True, "description": "Whether a successful command should be reported as changed."},
}

OPTIONAL_PARAM_OVERRIDES: dict[str, tuple[str, ...]] = {
    "local.command": ("cwd", "env", "shell", "timeout", "success_rc", "changed"),
    "remote.command": ("cwd", "timeout", "pty", "stdin", "encoding", "success_rc", "changed"),
}

DEFAULT_RESULT_FIELDS = {
    "changed": "Whether the plugin changed the target or controller state.",
    "message": "Human-readable result message.",
    "rc": "Process or command return code when applicable.",
    "stdout": "Captured standard output when applicable.",
    "stderr": "Captured standard error when applicable.",
    "data": "Plugin-specific structured result data.",
}

RESULT_FIELD_OVERRIDES: dict[str, dict[str, str]] = {
    "fs.exists": {"data.exists": "Boolean path existence result.", "data.path": "Checked remote path."},
    "fs.stat": {"data.exists": "Boolean path existence result.", "data.size": "Path size in bytes.", "data.mode": "POSIX mode.", "data.owner": "Owner name.", "data.group": "Group name."},
    "fs.read": {"stdout": "Remote file content.", "data.path": "Read remote path."},
    "fs.template": {"data.src": "Rendered template path.", "data.dest": "Remote destination path"},
    "db.sqlite.query": {"data.rows": "Fetched rows for SELECT-style statements.", "data.scalar": "First column of the first row when output=scalar.", "data.rowcount": "Driver rowcount when available."},
    "db.postgres.query": {"data.rows": "Fetched rows for SELECT-style statements.", "data.scalar": "First column of the first row when output=scalar.", "data.rowcount": "Driver rowcount when available."},
    "db.mysql.query": {"data.rows": "Fetched rows for SELECT-style statements.", "data.scalar": "First column of the first row when output=scalar.", "data.rowcount": "Driver rowcount when available."},
    "db.oracle.query": {"data.rows": "Fetched rows for SELECT-style statements.", "data.scalar": "First column of the first row when output=scalar.", "data.rowcount": "Driver rowcount when available."},
    "http.request": {"data.status": "HTTP response status code.", "data.body": "Decoded response body.", "data.headers": "Response headers."},
    "http.assert": {"data.status": "HTTP response status code.", "data.body": "Decoded response body."},
    "http.wait": {"data.status": "HTTP response status code.", "data.body": "Decoded response body."},
    "wait.tcp": {"data.host": "Checked host.", "data.port": "Checked TCP port."},
    "assert.tcp": {"data.host": "Checked host.", "data.port": "Checked TCP port."},
    "transfer.upload": {"data.src": "Local source path.", "data.dest": "Remote destination path"},
    "transfer.download": {"data.src": "Remote source path.", "data.dest": "Local destination path."},
    "user.exists": {"data.exists": "Whether the remote user exists.", "data.name": "Checked username."},
    "group.exists": {"data.exists": "Whether the remote group exists.", "data.name": "Checked group name."},
    "sudoers.dropin": {"data.path": "Installed sudoers drop-in path."},
    "transfer.sync": {"data.src": "Local source directory.", "data.dest": "Remote destination directory."},
}

SAMPLE_VALUES: dict[str, Any] = {
    "allow_replace_non_symlink": False,
    "append": True,
    "archive": "/tmp/app.tar.gz",
    "body": "payload",
    "command": "echo automax",
    "comment": "Application user",
    "commit": True,
    "compression": "gzip",
    "connect_timeout": 3,
    "connection": {"path": "/tmp/automax.sqlite"},
    "contains": "ok",
    "content": "managed by automax\n",
    "count": 0,
    "create": True,
    "create_home": False,
    "creates": "/opt/app/.installed",
    "cwd": "/tmp",
    "dest": "/tmp/dest",
    "encoding": "utf-8",
    "env": {"DEMO": "1"},
    "equals": "ok",
    "excludes": ["*.tmp"],
    "expected_status": 200,
    "fail_on_disabled": True,
    "fail_on_inactive": True,
    "fetch": "all",
    "force": True,
    "get_pty": False,
    "gid": 2000,
    "group": "app",
    "groups": ["app"],
    "headers": {"Accept": "application/json"},
    "home": "/var/lib/app",
    "host": "127.0.0.1",
    "ignore_missing": True,
    "interval": 2,
    "json": {"ok": True},
    "key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDemo automax@example",
    "password": "secret-password",
    "password_hash": "$6$rounds=4096$salt$hash",
    "validate": True,
    "line": "KEY=value",
    "lock": True,
    "manager": "auto",
    "max_depth": 2,
    "method": "GET",
    "min_free_mb": 1024,
    "min_free_percent": 10,
    "missing_ok": True,
    "mode": "0644",
    "name": "nginx",
    "not_contains": "error",
    "output": "rows",
    "overwrite": True,
    "owner": "app",
    "packages": ["curl"],
    "path": "/tmp/automax-demo",
    "pattern": "KEY=.*",
    "patterns": ["*.conf"],
    "pid": 1234,
    "port": 22,
    "preserve": True,
    "pty": False,
    "query": "SELECT 1 AS value",
    "query_params": [],
    "rc": 0,
    "recursive": True,
    "remove_home": False,
    "replacement": "KEY=new-value",
    "service": "sshd",
    "shell": True,
    "signal": "TERM",
    "source": "/var/log/app",
    "src": "/tmp/source",
    "state": "present",
    "statements": ["CREATE TABLE IF NOT EXISTS demo(id INTEGER)"],
    "status": 200,
    "stdin": "input\n",
    "strip_components": 1,
    "success_rc": 0,
    "sudo": True,
    "system": True,
    "timeout": 60,
    "type": "file",
    "uid": 2000,
    "unlock": True,
    "url": "https://example.invalid/health",
    "user": False,
    "validate_tls": True,
    "values": {"app_name": "demo"},
    "changed": True,
}

PLUGIN_EXAMPLES: dict[str, str] = {
    "fs.template": "use: fs.template\nwith:\n  src: ./templates/app.conf.j2\n  dest: /etc/myapp/app.conf\n  mode: '0644'\n  sudo: true",
    "db.sqlite.query": "use: db.sqlite.query\nwith:\n  connection:\n    path: /tmp/automax.sqlite\n  query: SELECT 1 AS value\n  output: rows",
    "remote.command": "use: remote.command\nwith:\n  command: systemctl is-active sshd\n  success_rc: 0",
    "ssh.authorized_key": "use: ssh.authorized_key\nwith:\n  user: deploy\n  key: '{{ vars.deploy_public_key }}'\n  state: present\n  sudo: true",
    "sudoers.dropin": "use: sudoers.dropin\nwith:\n  name: deploy-myapp\n  content: 'deploy ALL=(root) NOPASSWD: /bin/systemctl restart myapp'\n  validate: true\n  sudo: true",
    "local.command": "use: local.command\nwith:\n  command: echo automax\n  changed: false",
}


def apply_builtin_metadata(plugin: BasePlugin) -> BasePlugin:
    """Enrich a builtin plugin instance with complete public metadata."""
    optional_override = OPTIONAL_PARAM_OVERRIDES.get(plugin.name)
    if optional_override:
        plugin.optional_params = tuple(dict.fromkeys((*plugin.optional_params, *optional_override)))

    schema: dict[str, dict[str, Any]] = dict(getattr(plugin, "parameter_schema", {}) or {})
    for name in (*plugin.required_params, *plugin.optional_params):
        if name not in PARAMETERS:
            raise KeyError(f"missing metadata definition for parameter '{name}' used by {plugin.name}")
        merged = dict(PARAMETERS[name])
        merged.update(schema.get(name, {}))
        schema[name] = merged
    plugin.parameter_schema = schema

    result_fields = dict(DEFAULT_RESULT_FIELDS)
    result_fields.update(RESULT_FIELD_OVERRIDES.get(plugin.name, {}))
    plugin.result_fields = result_fields

    if not plugin.examples:
        plugin.examples = (_build_example(plugin),)
    return plugin


def _build_example(plugin: BasePlugin) -> str:
    configured = PLUGIN_EXAMPLES.get(plugin.name)
    if configured:
        return configured
    params = list(plugin.required_params)
    if not params:
        params = [name for name in plugin.optional_params[:2] if name in SAMPLE_VALUES]
    lines = [f"use: {plugin.name}"]
    if params:
        lines.append("with:")
        for name in params:
            lines.extend(_format_sample_value(name, SAMPLE_VALUES.get(name, "value"), indent="  "))
    return "\n".join(lines)


def _format_sample_value(name: str, value: Any, *, indent: str) -> list[str]:
    if isinstance(value, bool):
        return [f"{indent}{name}: {str(value).lower()}"]
    if isinstance(value, (int, float)):
        return [f"{indent}{name}: {value}"]
    if isinstance(value, list):
        lines = [f"{indent}{name}:"]
        lines.extend(f"{indent}  - {item}" for item in value)
        return lines
    if isinstance(value, dict):
        lines = [f"{indent}{name}:"]
        for key, item in value.items():
            if isinstance(item, bool):
                rendered = str(item).lower()
            else:
                rendered = str(item)
            lines.append(f"{indent}  {key}: {rendered}")
        return lines
    return [f"{indent}{name}: {value}"]
