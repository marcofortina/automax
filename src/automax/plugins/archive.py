# Copyright (C) 2026 Marco Fortina
# SPDX-License-Identifier: AGPL-3.0-or-later

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
            "data.archive.tar.create compression must be auto, none, gzip, bzip2 or xz"
        ) from exc


def _tar_extract_flag(archive: str, compression: str) -> str:
    if compression == "auto":
        return "-xf"
    create_flag = _tar_create_flag(archive, compression)
    return create_flag.replace("c", "x", 1)


def _stream_tool(path: str, compression: str, *, action: str) -> str:
    selected = compression
    if selected == "auto":
        suffixes = "".join(PurePosixPath(path).suffixes)
        if suffixes.endswith(".gz"):
            selected = "gzip"
        elif suffixes.endswith(".bz2"):
            selected = "bzip2"
        elif suffixes.endswith(".xz"):
            selected = "xz"
        else:
            raise PluginValidationError(
                f"archive.{action} compression auto requires .gz, .bz2 or .xz suffix"
            )
    mapping = {
        "gzip": "gzip",
        "gz": "gzip",
        "bzip2": "bzip2",
        "bz2": "bzip2",
        "xz": "xz",
        "zstd": "zstd",
        "zst": "zstd",
    }
    try:
        return mapping[selected]
    except KeyError as exc:
        raise PluginValidationError(
            f"archive.{action} compression must be auto, gzip, bzip2 or xz"
        ) from exc


class ArchiveTarPlugin(BasePlugin):
    """Create a remote tar archive."""

    name = "data.archive.tar.create"
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

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        flag = _tar_create_flag(str(params["dest"]), str(params.get("compression", "auto")))
        excludes = " ".join(f"--exclude={quote(item)}" for item in _as_list(params.get("excludes")))
        sources = _quote_many(_as_list(params["source"]))
        command = " ".join(part for part in ("tar", flag, quote(params["dest"]), excludes, sources) if part)
        return apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="data.archive.tar.create requires an SSH session")
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="data.archive.tar.create failed",
            data={"source": params["source"], "dest": params["dest"]},
        )


class ArchiveUntarPlugin(BasePlugin):
    """Extract a remote tar archive."""

    name = "data.archive.tar.extract"
    description = "Extract a remote tar archive."
    required_params = ("archive", "dest")
    optional_params = ("compression", "strip_components", "creates", "cwd")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _tar_extract_flag(str(params["archive"]), str(params.get("compression", "auto")))
        if "strip_components" in params and int(params["strip_components"]) < 0:
            raise PluginValidationError("data.archive.tar.extract strip_components must be >= 0")

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: untar {params.get('archive')} to {params.get('dest')}",
            data={"params": params},
        )

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
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
        return apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="data.archive.tar.extract requires an SSH session")
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="data.archive.tar.extract failed",
            data={"archive": params["archive"], "dest": params["dest"]},
        )


class ArchiveCompressPlugin(BasePlugin):
    """Compress one remote file to gzip, bzip2 or xz stream output."""

    name = "archive.compress"
    description = "Compress one remote file to gzip, bzip2 or xz."
    required_params = ("source", "dest")
    optional_params = ("compression", "force", "creates", "cwd")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _stream_tool(str(params.get("dest")), str(params.get("compression", "auto")), action="compress")

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: compress {params.get('source')} to {params.get('dest')}",
            data={"params": params},
        )

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        tool = _stream_tool(str(params["dest"]), str(params.get("compression", "auto")), action="compress")
        source = quote(params["source"])
        dest = quote(params["dest"])
        body = f"{tool} -c {source} > {dest} && echo {CHANGE_MARKER}"
        if params.get("creates"):
            command = f"test -e {quote(params['creates'])} || {{ {body}; }}"
        elif bool(params.get("force", False)):
            command = f"{{ {body}; }}"
        else:
            command = f"test -e {dest} || {{ {body}; }}"
        return apply_cwd(command, context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="archive.compress requires an SSH session")
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="archive.compress failed",
            data={"source": params["source"], "dest": params["dest"]},
        )


class ArchiveDecompressPlugin(BasePlugin):
    """Decompress one remote gzip, bzip2 or xz file to a destination file."""

    name = "archive.decompress"
    description = "Decompress one remote gzip, bzip2 or xz file."
    required_params = ("archive", "dest")
    optional_params = ("compression", "force", "creates", "cwd")
    opens_remote_session = True

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(params)
        _stream_tool(str(params.get("archive")), str(params.get("compression", "auto")), action="decompress")

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return PluginResult.success(
            changed=False,
            message=f"dry-run: decompress {params.get('archive')} to {params.get('dest')}",
            data={"params": params},
        )

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        tool = _stream_tool(str(params["archive"]), str(params.get("compression", "auto")), action="decompress")
        archive = quote(params["archive"])
        dest = quote(params["dest"])
        body = f"{tool} -dc {archive} > {dest} && echo {CHANGE_MARKER}"
        if params.get("creates"):
            command = f"test -e {quote(params['creates'])} || {{ {body}; }}"
        elif bool(params.get("force", False)):
            command = f"{{ {body}; }}"
        else:
            command = f"test -e {dest} || {{ {body}; }}"
        return apply_cwd(command, context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="archive.decompress requires an SSH session")
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="archive.decompress failed",
            data={"archive": params["archive"], "dest": params["dest"]},
        )


class ArchiveZipPlugin(BasePlugin):
    """Create a remote zip archive."""

    name = "data.archive.zip.create"
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

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        recursive = "-r" if bool(params.get("recursive", True)) else ""
        sources = _quote_many(_as_list(params["source"]))
        excludes = ""
        if params.get("excludes"):
            excludes = "-x " + _quote_many(_as_list(params.get("excludes")))
        command = " ".join(
            part for part in ("zip", recursive, quote(params["dest"]), sources, excludes) if part
        )
        return apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="data.archive.zip.create requires an SSH session")
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="data.archive.zip.create failed",
            data={"source": params["source"], "dest": params["dest"]},
        )


class ArchiveUnzipPlugin(BasePlugin):
    """Extract a remote zip archive."""

    name = "data.archive.zip.extract"
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

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        mode = "-o" if bool(params.get("overwrite", False)) else "-n"
        command = (
            f"mkdir -p {quote(params['dest'])} && "
            f"unzip {mode} {quote(params['archive'])} -d {quote(params['dest'])}"
        )
        return apply_cwd(_guarded(command, params.get("creates")), context, params.get("cwd"))

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [self._command(params, context)]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        self.validate(params)
        if context.dry_run:
            return self.dry_run(params, context)
        if context.ssh_client is None:
            return PluginResult.failure(message="data.archive.zip.extract requires an SSH session")
        rc, out, err = exec_remote(context, self._command(params, context))
        return result_from_remote(
            rc=rc,
            stdout=out,
            stderr=err,
            message="data.archive.zip.extract failed",
            data={"archive": params["archive"], "dest": params["dest"]},
        )

# Harden archive extraction with optional checksum and safe path validation.


def _checksum_command(path: str, expected: str) -> str:
    return f"sha256sum {quote(path)} | awk '{{print $1}}' | grep -Fix -- {quote(expected)}"


def _tar_safe_command(archive: str) -> str:
    return f"tar -tf {quote(archive)} | awk 'BEGIN{{bad=0}} /^\\// || /(^|\\/)\\.\\.($|\\//) {{bad=1; print \"unsafe archive path: \" $0 > \"/dev/stderr\"}} END{{exit bad}}'"


def _zip_safe_command(archive: str) -> str:
    return f"unzip -Z1 {quote(archive)} | awk 'BEGIN{{bad=0}} /^\\// || /(^|\\/)\\.\\.($|\\//) {{bad=1; print \"unsafe archive path: \" $0 > \"/dev/stderr\"}} END{{exit bad}}'"


def _post_extract_attrs(dest: str, params: Dict[str, Any]) -> list[str]:
    cmds = []
    if params.get("owner") or params.get("group"):
        spec = f"{params.get('owner', '')}:{params.get('group', '')}"
        cmds.append(f"chown -R {quote(spec)} {quote(dest)}")
    if params.get("mode"):
        cmds.append(f"chmod -R {quote(params['mode'])} {quote(dest)}")
    return cmds


def _hardened_untar_command(self: ArchiveUntarPlugin, params: Dict[str, Any], context: ExecutionContext) -> str:
    flag = _tar_extract_flag(str(params["archive"]), str(params.get("compression", "auto")))
    parts = []
    if params.get("checksum_verify"):
        parts.append(_checksum_command(str(params["archive"]), str(params["checksum_verify"])))
    if bool(params.get("safe_extract", True)):
        parts.append(_tar_safe_command(str(params["archive"])))
    strip = f"--strip-components={int(params['strip_components'])}" if "strip_components" in params else ""
    excludes = " ".join(f"--exclude={quote(item)}" for item in _as_list(params.get("exclude")))
    includes = " ".join(quote(item) for item in _as_list(params.get("include")))
    extract = " ".join(part for part in (f"mkdir -p {quote(params['dest'])} && tar", flag, quote(params["archive"]), "-C", quote(params["dest"]), strip, excludes, includes) if part)
    parts.append(extract)
    parts.extend(_post_extract_attrs(str(params["dest"]), params))
    return apply_cwd(_guarded(" && ".join(parts), params.get("creates")), context, params.get("cwd"))


def _hardened_unzip_command(self: ArchiveUnzipPlugin, params: Dict[str, Any], context: ExecutionContext) -> str:
    parts = []
    if params.get("checksum_verify"):
        parts.append(_checksum_command(str(params["archive"]), str(params["checksum_verify"])))
    if bool(params.get("safe_extract", True)):
        parts.append(_zip_safe_command(str(params["archive"])))
    mode = "-o" if bool(params.get("overwrite", False)) else "-n"
    includes = " ".join(quote(item) for item in _as_list(params.get("include")))
    excludes = " ".join(f"-x {quote(item)}" for item in _as_list(params.get("exclude")))
    parts.append(" ".join(part for part in (f"mkdir -p {quote(params['dest'])} && unzip", mode, quote(params["archive"]), includes, "-d", quote(params["dest"]), excludes) if part))
    parts.extend(_post_extract_attrs(str(params["dest"]), params))
    return apply_cwd(_guarded(" && ".join(parts), params.get("creates")), context, params.get("cwd"))


class HardenedArchiveUntarPlugin(ArchiveUntarPlugin):
    """data.archive.tar.extract with checksum, safe extraction and ownership controls."""

    optional_params = ("compression", "strip_components", "creates", "cwd", "safe_extract", "checksum_verify", "include", "exclude", "owner", "group", "mode")

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return _hardened_untar_command(self, params, context)


class HardenedArchiveUnzipPlugin(ArchiveUnzipPlugin):
    """data.archive.zip.extract with checksum, safe extraction and ownership controls."""

    optional_params = ("overwrite", "creates", "cwd", "safe_extract", "checksum_verify", "include", "exclude", "owner", "group", "mode")

    def _command(self, params: Dict[str, Any], context: ExecutionContext) -> str:
        return _hardened_unzip_command(self, params, context)


class ArchiveTarListPlugin(BasePlugin):
    """List files inside a remote tar archive."""

    name = "data.archive.tar.list"
    description = "List files inside a remote tar archive."
    required_params = ("archive",)
    optional_params = ("compression", "cwd")
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        flag = _tar_extract_flag(str(params["archive"]), str(params.get("compression", "auto"))).replace("x", "t", 1)
        command = f"tar {flag} {quote(params['archive'])}"
        return [apply_cwd(command, context, params.get("cwd"))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="data.archive.tar.list failed", data={"entries": [line for line in out.splitlines() if line]})


class ArchiveTarCheckPlugin(ArchiveTarListPlugin):
    """Assert a remote tar archive is readable and optionally contains entries."""

    name = "data.archive.tar.check"
    description = "Assert a remote tar archive is readable and optionally contains entries."
    optional_params = ("compression", "contains", "cwd")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        commands = super().manual_commands(params, context)
        entries = _as_list(params.get("contains"))
        if entries:
            archive = quote(params["archive"])
            flag = _tar_extract_flag(str(params["archive"]), str(params.get("compression", "auto"))).replace("x", "t", 1)
            checks = " && ".join(f"tar {flag} {archive} | grep -Fx -- {quote(item)} >/dev/null" for item in entries)
            commands = [checks]
        return commands


class ArchiveZipListPlugin(BasePlugin):
    """List files inside a remote zip archive."""

    name = "data.archive.zip.list"
    description = "List files inside a remote zip archive."
    required_params = ("archive",)
    optional_params = ("cwd",)
    opens_remote_session = True
    supports_check_mode = True

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [apply_cwd(f"unzip -Z1 {quote(params['archive'])}", context, params.get("cwd"))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message="data.archive.zip.list failed", data={"entries": [line for line in out.splitlines() if line]})


class ArchiveZipCheckPlugin(ArchiveZipListPlugin):
    """Assert a remote zip archive is readable and optionally contains entries."""

    name = "data.archive.zip.check"
    description = "Assert a remote zip archive is readable and optionally contains entries."
    optional_params = ("contains", "cwd")

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        if params.get("contains"):
            archive = quote(params["archive"])
            checks = " && ".join(f"unzip -Z1 {archive} | grep -Fx -- {quote(item)} >/dev/null" for item in _as_list(params.get("contains")))
            return [apply_cwd(checks, context, params.get("cwd"))]
        return [apply_cwd(f"unzip -t {quote(params['archive'])}", context, params.get("cwd"))]


class _FixedCompressionMixin:
    compression = ""
    tool = ""

    def _fixed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        copied = dict(params)
        copied["compression"] = self.compression
        return copied

    def validate(self, params: Dict[str, Any]) -> None:
        super().validate(self._fixed(params))

    def dry_run(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return super().dry_run(self._fixed(params), context)

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        return super().manual_commands(self._fixed(params), context)

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        return super().execute(self._fixed(params), context)


class CompressionGzipCompressPlugin(_FixedCompressionMixin, ArchiveCompressPlugin):
    name = "data.compression.gzip.compress"
    description = "Compress one remote file with gzip."
    compression = "gzip"


class CompressionGzipDecompressPlugin(_FixedCompressionMixin, ArchiveDecompressPlugin):
    name = "data.compression.gzip.decompress"
    description = "Decompress one remote gzip file."
    compression = "gzip"


class CompressionBzip2CompressPlugin(_FixedCompressionMixin, ArchiveCompressPlugin):
    name = "data.compression.bzip2.compress"
    description = "Compress one remote file with bzip2."
    compression = "bzip2"


class CompressionBzip2DecompressPlugin(_FixedCompressionMixin, ArchiveDecompressPlugin):
    name = "data.compression.bzip2.decompress"
    description = "Decompress one remote bzip2 file."
    compression = "bzip2"


class CompressionXzCompressPlugin(_FixedCompressionMixin, ArchiveCompressPlugin):
    name = "data.compression.xz.compress"
    description = "Compress one remote file with xz."
    compression = "xz"


class CompressionXzDecompressPlugin(_FixedCompressionMixin, ArchiveDecompressPlugin):
    name = "data.compression.xz.decompress"
    description = "Decompress one remote xz file."
    compression = "xz"


class CompressionZstdCompressPlugin(_FixedCompressionMixin, ArchiveCompressPlugin):
    name = "data.compression.zstd.compress"
    description = "Compress one remote file with zstd."
    compression = "zstd"


class CompressionZstdDecompressPlugin(_FixedCompressionMixin, ArchiveDecompressPlugin):
    name = "data.compression.zstd.decompress"
    description = "Decompress one remote zstd file."
    compression = "zstd"


class _CompressionCheckPlugin(BasePlugin):
    required_params = ("path",)
    optional_params = ("cwd",)
    opens_remote_session = True
    supports_check_mode = True
    tool = ""

    def manual_commands(self, params: Dict[str, Any], context: ExecutionContext) -> list[str]:
        self.validate(params)
        return [apply_cwd(f"{self.tool} -t {quote(params['path'])}", context, params.get("cwd"))]

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> PluginResult:
        rc, out, err = exec_remote(context, self.manual_commands(params, context)[0])
        return result_from_remote(rc=rc, stdout=out, stderr=err, message=f"{self.name} failed", data={"path": str(params["path"])})


class CompressionGzipCheckPlugin(_CompressionCheckPlugin):
    name = "data.compression.gzip.check"
    description = "Assert a remote gzip file is readable."
    tool = "gzip"


class CompressionBzip2CheckPlugin(_CompressionCheckPlugin):
    name = "data.compression.bzip2.check"
    description = "Assert a remote bzip2 file is readable."
    tool = "bzip2"


class CompressionXzCheckPlugin(_CompressionCheckPlugin):
    name = "data.compression.xz.check"
    description = "Assert a remote xz file is readable."
    tool = "xz"


class CompressionZstdCheckPlugin(_CompressionCheckPlugin):
    name = "data.compression.zstd.check"
    description = "Assert a remote zstd file is readable."
    tool = "zstd"
