# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Additional remote filesystem plugins.
"""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
from typing import Any, Dict

from jinja2 import StrictUndefined, Template

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.file_utils import install_uploaded_file, upload_text_to_temp
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote


def _content_diff(path: str, content: str) -> str:
    """Return a create/update preview diff without reading the remote target."""
    return "".join(
        unified_diff(
            [],
            content.splitlines(keepends=True),
            fromfile=f"{path} (current)",
            tofile=f"{path} (desired)",
        )
    )


def _render_template_content(params: Dict[str, Any], context: ExecutionContext) -> tuple[str, str]:
    encoding = str(params.get("encoding", "utf-8"))
    template_path = Path(str(params["src"])).expanduser()
    if not template_path.is_file():
        raise FileNotFoundError(f"template not found: {template_path}")
    template = Template(template_path.read_text(encoding=encoding), undefined=StrictUndefined)
    values = params.get("values", {}) or {}
    if not isinstance(values, dict):
        raise PluginValidationError("fs.template values must be a mapping")
    rendered = template.render(
        job=context.job,
        task=context.task,
        step=context.step,
        substep=context.substep,
        target=context.target,
        server=context.target,
        vars=context.vars,
        outputs=context.outputs,
        secrets=context.secrets,
        step_state=context.step_state,
        values=values,
    )
    return str(template_path), rendered


class FsExistsPlugin(BasePlugin):
    """Check whether a remote path exists without failing when it does not."""

    name = "fs.exists"
    description = "Check whether a remote path exists."
    required_params = ("path",)
    optional_params = ("type", "cwd")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        test_flag = {"file": "-f", "directory": "-d", "dir": "-d", "path": "-e", "any": "-e"}.get(
            str(params.get("type", "any"))
        )
        if test_flag is None:
            raise PluginValidationError("fs.exists type must be file, directory, dir, path or any")
        command = apply_cwd(f"test {test_flag} {quote(params['path'])}", context, params.get("cwd"))
        rc, out, err = exec_remote(context, command)
        exists = rc == 0
        return PluginResult.success(
            changed=False,
            rc=0,
            stdout=out,
            stderr="" if exists else err,
            data={"exists": exists, "path": params["path"]},
        )


class FsStatPlugin(BasePlugin):
    """Read POSIX stat metadata for a remote path."""

    name = "fs.stat"
    description = "Read remote path metadata."
    required_params = ("path",)
    optional_params = ("missing_ok", "cwd")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        command = apply_cwd(
            "stat -c '%F|%s|%a|%U|%G|%Y|%n' " + quote(params["path"]),
            context,
            params.get("cwd"),
        )
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            if bool(params.get("missing_ok", False)):
                return PluginResult.success(changed=False, data={"exists": False, "path": params["path"]})
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.stat failed")
        parts = out.strip().split("|", 6)
        keys = ("type", "size", "mode", "owner", "group", "mtime", "path")
        data = dict(zip(keys, parts))
        data["exists"] = True
        if "size" in data:
            data["size"] = int(data["size"])
        if "mtime" in data:
            data["mtime"] = int(data["mtime"])
        return PluginResult.success(changed=False, stdout=out, data=data)


class FsReadPlugin(BasePlugin):
    """Read a remote text file."""

    name = "fs.read"
    description = "Read a remote file."
    required_params = ("path",)
    optional_params = ("cwd",)
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        command = apply_cwd(f"cat {quote(params['path'])}", context, params.get("cwd"))
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.read failed")
        return PluginResult.success(changed=False, stdout=out, data={"content": out, "path": params["path"]})


class FsWritePlugin(BasePlugin):
    """Write text content to a remote file using SFTP plus atomic install/move."""

    name = "fs.write"
    description = "Write text content to a remote file."
    required_params = ("path", "content")
    optional_params = ("mode", "owner", "group", "sudo", "encoding")
    opens_remote_session = True

    def diff_preview(
        self, params: Dict[str, Any], context: ExecutionContext
    ) -> list[Dict[str, Any]]:
        self.validate(params)
        content = str(params.get("content", ""))
        path = str(params["path"])
        return [{"path": path, "diff": _content_diff(path, content), "kind": "unified"}]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        content = str(params.get("content", ""))
        temp_path = upload_text_to_temp(context, content, encoding=str(params.get("encoding", "utf-8")))
        rc, out, err = install_uploaded_file(
            context,
            temp_path,
            str(params["path"]),
            sudo=bool(params.get("sudo", False)),
            mode=params.get("mode"),
            owner=params.get("owner"),
            group=params.get("group"),
        )
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.write failed",
            data={"path": params["path"]},
        )


class FsTemplatePlugin(BasePlugin):
    """Render a local Jinja2 template and write it to a remote file."""

    name = "fs.template"
    description = "Render a local Jinja2 template to a remote file."
    required_params = ("src", "dest")
    optional_params = ("mode", "owner", "group", "sudo", "encoding", "values")
    parameter_schema = {
        "src": {"type": "path", "description": "Local Jinja2 template path on the controller."},
        "dest": {"type": "path", "description": "Remote destination file path."},
        "mode": {"type": "string", "description": "Optional remote file mode, for example 0644."},
        "owner": {"type": "string", "description": "Optional remote file owner."},
        "group": {"type": "string", "description": "Optional remote file group."},
        "sudo": {"type": "boolean", "default": False, "description": "Install the rendered file with sudo."},
        "encoding": {"type": "string", "default": "utf-8", "description": "Template and upload encoding."},
        "values": {"type": "mapping", "description": "Additional values exposed to the template as values.*."},
    }
    examples = (
        "use: fs.template\nwith:\n  src: ./templates/app.conf.j2\n  dest: /etc/myapp/app.conf\n  mode: '0644'\n  sudo: true",
    )
    result_fields = {"data.src": "Rendered template path", "data.dest": "Remote destination path"}
    opens_remote_session = True

    def diff_preview(
        self, params: Dict[str, Any], context: ExecutionContext
    ) -> list[Dict[str, Any]]:
        self.validate(params)
        src, rendered = _render_template_content(params, context)
        dest = str(params["dest"])
        return [
            {
                "path": dest,
                "source": src,
                "diff": _content_diff(dest, rendered),
                "kind": "unified",
            }
        ]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        encoding = str(params.get("encoding", "utf-8"))
        try:
            template_path, rendered = _render_template_content(params, context)
        except FileNotFoundError as exc:
            return PluginResult.failure(message=str(exc))
        temp_path = upload_text_to_temp(context, rendered, encoding=encoding)
        rc, out, err = install_uploaded_file(
            context,
            temp_path,
            str(params["dest"]),
            sudo=bool(params.get("sudo", False)),
            mode=params.get("mode"),
            owner=params.get("owner"),
            group=params.get("group"),
        )
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.template failed",
            data={"src": template_path, "dest": params["dest"]},
        )


class FsLinePlugin(BasePlugin):
    """Ensure one exact line is present or absent in a remote file."""

    name = "fs.line"
    description = "Ensure an exact line is present or absent in a remote file."
    required_params = ("path", "line")
    optional_params = ("state", "create", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        state = str(params.get("state", "present"))
        if state not in {"present", "absent"}:
            raise PluginValidationError("fs.line state must be present or absent")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        script = r'''
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
line = sys.argv[2]
state = sys.argv[3]
create = sys.argv[4].lower() == "true"
if not path.exists():
    if not create and state == "present":
        raise FileNotFoundError(str(path))
    lines = []
else:
    lines = path.read_text(encoding="utf-8").splitlines()
changed = False
if state == "present":
    if line not in lines:
        lines.append(line)
        changed = True
else:
    new_lines = [item for item in lines if item != line]
    changed = len(new_lines) != len(lines)
    lines = new_lines
if changed:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print("__AUTOMAX_CHANGED__")
'''
        python = "sudo -n python3" if bool(params.get("sudo", False)) else "python3"
        command = (
            f"{python} - {quote(params['path'])} {quote(params['line'])} "
            f"{quote(params.get('state', 'present'))} {quote(str(bool(params.get('create', False))))} "
            f"<<'PY'\n{script}\nPY"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="fs.line failed")


class FsReplacePlugin(BasePlugin):
    """Replace text in a remote file using a Python regular expression."""

    name = "fs.replace"
    description = "Replace text in a remote file using a regex pattern."
    required_params = ("path", "pattern", "replacement")
    optional_params = ("count", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        script = r'''
import pathlib
import re
import sys
path = pathlib.Path(sys.argv[1])
pattern = sys.argv[2]
replacement = sys.argv[3]
count = int(sys.argv[4])
text = path.read_text(encoding="utf-8")
new_text, changed_count = re.subn(pattern, replacement, text, count=count)
if changed_count:
    path.write_text(new_text, encoding="utf-8")
    print("__AUTOMAX_CHANGED__")
print(changed_count)
'''
        python = "sudo -n python3" if bool(params.get("sudo", False)) else "python3"
        command = (
            f"{python} - {quote(params['path'])} {quote(params['pattern'])} "
            f"{quote(params['replacement'])} {quote(params.get('count', 0))} <<'PY'\n{script}\nPY"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="fs.replace failed")


class FsMovePlugin(BasePlugin):
    """Move or rename a remote path."""

    name = "fs.move"
    description = "Move or rename a remote path."
    required_params = ("src", "dest")
    optional_params = ("overwrite", "sudo")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        sudo = "sudo -n " if bool(params.get("sudo", False)) else ""
        overwrite = bool(params.get("overwrite", True))
        flag = "-f" if overwrite else "-n"
        command = (
            f"if test -e {quote(params['dest'])} && ! test -e {quote(params['src'])}; then :; "
            f"else {sudo}mv {flag} {quote(params['src'])} {quote(params['dest'])} && echo {CHANGE_MARKER}; fi"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="fs.move failed")


class FsSymlinkCreatePlugin(BasePlugin):
    """Create or update a remote symbolic link with conservative replacement rules."""

    name = "fs.symlink.create"
    description = "Create or update a remote symbolic link."
    required_params = ("src", "dest")
    optional_params = ("force", "allow_replace_non_symlink", "sudo")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        dest = str(params["dest"])
        if not dest or dest == "/":
            raise PluginValidationError("fs.symlink.create dest must not be empty or /")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        script = f"""
set -eu
src=$1
dest=$2
force=$3
allow_replace_non_symlink=$4
use_sudo=$5
run() {{
    if [ \"$use_sudo\" = \"true\" ]; then
        sudo -n \"$@\"
    else
        \"$@\"
    fi
}}
if [ -L \"$dest\" ]; then
    current=$(readlink \"$dest\")
    if [ \"$current\" = \"$src\" ]; then
        exit 0
    fi
    if [ \"$force\" != \"true\" ]; then
        echo \"refusing to replace existing symlink without force: $dest -> $current\" >&2
        exit 1
    fi
    run rm -f \"$dest\"
    run ln -s \"$src\" \"$dest\"
    echo {CHANGE_MARKER}
elif [ -e \"$dest\" ]; then
    if [ \"$force\" = \"true\" ] && [ \"$allow_replace_non_symlink\" = \"true\" ]; then
        run rm -rf \"$dest\"
        run ln -s \"$src\" \"$dest\"
        echo {CHANGE_MARKER}
    else
        echo \"refusing to replace non-symlink path: $dest\" >&2
        exit 1
    fi
else
    run ln -s \"$src\" \"$dest\"
    echo {CHANGE_MARKER}
fi
"""
        command = (
            f"sh -s -- {quote(params['src'])} {quote(params['dest'])} "
            f"{quote(str(bool(params.get('force', False))).lower())} "
            f"{quote(str(bool(params.get('allow_replace_non_symlink', False))).lower())} "
            f"{quote(str(bool(params.get('sudo', False))).lower())} <<'SH'\n{script}\nSH"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.symlink.create failed",
            data={"src": params["src"], "dest": params["dest"]},
        )


class FsSymlinkRemovePlugin(BasePlugin):
    """Remove a remote symbolic link without deleting regular files or directories."""

    name = "fs.symlink.remove"
    description = "Remove a remote symbolic link safely."
    required_params = ("path",)
    optional_params = ("sudo",)
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        path = str(params["path"])
        if not path or path == "/":
            raise PluginValidationError("fs.symlink.remove path must not be empty or /")

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        script = f"""
set -eu
path=$1
use_sudo=$2
run() {{
    if [ \"$use_sudo\" = \"true\" ]; then
        sudo -n \"$@\"
    else
        \"$@\"
    fi
}}
if [ -L \"$path\" ]; then
    run rm -f \"$path\"
    echo {CHANGE_MARKER}
elif [ ! -e \"$path\" ]; then
    exit 0
else
    echo \"refusing to remove non-symlink path: $path\" >&2
    exit 1
fi
"""
        command = (
            f"sh -s -- {quote(params['path'])} "
            f"{quote(str(bool(params.get('sudo', False))).lower())} <<'SH'\n{script}\nSH"
        )
        rc, out, err = exec_remote(context, command)
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="fs.symlink.remove failed",
            data={"path": params["path"]},
        )


class FsFindPlugin(BasePlugin):
    """Find remote paths and return the matching path list."""

    name = "fs.find"
    description = "Find remote paths."
    required_params = ("path",)
    optional_params = ("patterns", "type", "max_depth", "cwd")
    opens_remote_session = True

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        parts = ["find", quote(params["path"])]
        if params.get("max_depth") is not None:
            parts.extend(["-maxdepth", quote(params["max_depth"])])
        file_type = params.get("type")
        if file_type:
            type_flag = {"file": "f", "directory": "d", "dir": "d", "symlink": "l"}.get(str(file_type))
            if not type_flag:
                raise PluginValidationError("fs.find type must be file, directory, dir or symlink")
            parts.extend(["-type", type_flag])
        patterns = params.get("patterns") or params.get("pattern")
        if patterns:
            items = patterns if isinstance(patterns, list) else [patterns]
            if len(items) == 1:
                parts.extend(["-name", quote(items[0])])
            else:
                expr = " -o ".join(f"-name {quote(item)}" for item in items)
                parts.append(f"\\( {expr} \\)")
        command = apply_cwd(" ".join(parts), context, params.get("cwd"))
        rc, out, err = exec_remote(context, command)
        if rc != 0:
            return PluginResult.failure(rc=rc, stdout=out, stderr=err, message="fs.find failed")
        paths = [line for line in out.splitlines() if line]
        return PluginResult.success(changed=False, stdout=out, data={"paths": paths})
