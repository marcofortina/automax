"""
Remote archive macro plugins.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Dict, Iterable

from automax.core.models import ExecutionContext, PluginResult
from automax.plugins.base import BasePlugin, PluginValidationError
from automax.plugins.remote_utils import CHANGE_MARKER, apply_cwd, exec_remote, quote, result_from_remote


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _quote_many(values: Iterable[Any]) -> str:
    return " ".join(quote(value) for value in values)


def _guarded(command: str, guard: Any | None) -> str:
    body = f"{command} && echo {CHANGE_MARKER}"
    if guard:
        return f"test -e {quote(guard)} || {{ {body}; }}"
    return f"{{ {body}; }}"


def _tar_create_flag(dest: str, compression: str) -> str:
    selected = compression
    if selected == "auto":
        suffixes = "".join(PurePosixPath(dest).suffixes)
        if suffixes.endswith(".tar.gz") or dest.endswith(".tgz"):
            selected = "gzip"
        elif suffixes.endswith(".tar.bz2") or dest.endswith(".tbz2"):
            selected = "bzip2"
        elif suffixes.endswith(".tar.xz") or dest.endswith(".txz"):
            selected = "xz"
        else:
            selected = "none"
    mapping = {
        "none": "-cf",
        "gzip": "-czf",
        "gz": "-czf",
        "bzip2": "-cjf",
        "bz2": "-cjf",
        "xz": "-cJf",
    }
    try:
        return mapping[selected]
    except KeyError as exc:
        raise PluginValidationError(
            "archive.tar compression must be auto, none, gzip, bzip2 or xz"
        ) from exc


def _tar_extract_flag(archive: str, compression: str) -> str:
    if compression == "auto":
        return "-xf"
    create_flag = _tar_create_flag(archive, compression)
    return create_flag.replace("c", "x", 1)


class ArchiveTarPlugin(BasePlugin):
    """Create a remote tar archive."""

    name = "archive.tar"
    description = "Create a remote tar archive."
    required_params = ("source", "dest")
    optional_params = ("compression", "excludes", "creates", "cwd")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _tar_create_flag(str(params["dest"]), str(params.get("compression", "auto")))

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: tar {params.get('source')} to {params.get('dest')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="archive.tar requires an SSH session")
        flag = _tar_create_flag(str(params["dest"]), str(params.get("compression", "auto")))
        excludes = " ".join(f"--exclude={quote(item)}" for item in _as_list(params.get("excludes")))
        sources = _quote_many(_as_list(params["source"]))
        command = " ".join(part for part in ("tar", flag, quote(params["dest"]), excludes, sources) if part)
        rc, out, err = exec_remote(
            context,
            apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd")),
        )
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="archive.tar failed",
            data={"source": params["source"], "dest": params["dest"]},
        )


class ArchiveUntarPlugin(BasePlugin):
    """Extract a remote tar archive."""

    name = "archive.untar"
    description = "Extract a remote tar archive."
    required_params = ("archive", "dest")
    optional_params = ("compression", "strip_components", "creates", "cwd")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _tar_extract_flag(str(params["archive"]), str(params.get("compression", "auto")))
        if "strip_components" in params and int(params["strip_components"]) < 0:
            raise PluginValidationError("archive.untar strip_components must be >= 0")

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: untar {params.get('archive')} to {params.get('dest')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="archive.untar requires an SSH session")
        flag = _tar_extract_flag(str(params["archive"]), str(params.get("compression", "auto")))
        strip = ""
        if "strip_components" in params:
            strip = f"--strip-components={int(params['strip_components'])}"
        command = " ".join(
            part
            for part in (
                f"mkdir -p {quote(params['dest'])} && tar",
                flag,
                quote(params["archive"]),
                "-C",
                quote(params["dest"]),
                strip,
            )
            if part
        )
        rc, out, err = exec_remote(
            context,
            apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd")),
        )
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="archive.untar failed",
            data={"archive": params["archive"], "dest": params["dest"]},
        )


class ArchiveZipPlugin(BasePlugin):
    """Create a remote zip archive."""

    name = "archive.zip"
    description = "Create a remote zip archive."
    required_params = ("source", "dest")
    optional_params = ("recursive", "excludes", "creates", "cwd")
    opens_remote_session = True

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: zip {params.get('source')} to {params.get('dest')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="archive.zip requires an SSH session")
        recursive = "-r" if bool(params.get("recursive", True)) else ""
        sources = _quote_many(_as_list(params["source"]))
        excludes = ""
        if params.get("excludes"):
            excludes = "-x " + _quote_many(_as_list(params.get("excludes")))
        command = " ".join(
            part for part in ("zip", recursive, quote(params["dest"]), sources, excludes) if part
        )
        rc, out, err = exec_remote(
            context,
            apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd")),
        )
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="archive.zip failed",
            data={"source": params["source"], "dest": params["dest"]},
        )


class ArchiveUnzipPlugin(BasePlugin):
    """Extract a remote zip archive."""

    name = "archive.unzip"
    description = "Extract a remote zip archive."
    required_params = ("archive", "dest")
    optional_params = ("overwrite", "creates", "cwd")
    opens_remote_session = True

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: unzip {params.get('archive')} to {params.get('dest')}",
            data={"params": params},
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="archive.unzip requires an SSH session")
        mode = "-o" if bool(params.get("overwrite", False)) else "-n"
        command = (
            f"mkdir -p {quote(params['dest'])} && "
            f"unzip {mode} {quote(params['archive'])} -d {quote(params['dest'])}"
        )
        rc, out, err = exec_remote(
            context,
            apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd")),
        )
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="archive.unzip failed",
            data={"archive": params["archive"], "dest": params["dest"]},
        )
