"""
Plugin for compressing files and directories.
"""

import gzip
from pathlib import Path
import shutil
import tarfile
from typing import Any, Dict
import zipfile

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class CompressFilePlugin(BasePlugin):
    """
    Compress files and directories using gzip, tar, or zip.

    Returns:
        Dictionary containing:
            - source_path (str): The original path that was compressed
            - output_path (str): The path of the created compressed file
            - format (str): The format used for compression (gzip, tar, zip)
            - compression_level (int): The compression level used
            - original_size (int): The size of the original file/directory in bytes
            - compressed_size (int): The size of the compressed file in bytes
            - compression_ratio (float): The ratio of compressed size to original size
            - status (str): "success" if the operation was successful

    Raises:
        PluginExecutionError: If compression fails due to missing files,
                            permission issues, unsupported formats, or other errors.

    """

    METADATA = PluginMetadata(
        name="compress_file",
        version="2.0.0",
        description="Compress files or directories using gzip, tar, or zip",
        author="Marco Fortina",
        category="file_operations",
        tags=["compress", "archive", "file", "gzip", "tar", "zip"],
        required_config=["source_path", "output_path"],
        optional_config=["format", "compression_level"],
    )

    SCHEMA = {
        "source_path": {"type": str, "required": True},
        "output_path": {"type": str, "required": True},
        "format": {"type": str, "required": False},
        "compression_level": {"type": int, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Compress a file or directory.

        Returns:
            dict: source_path, output_path, format, compression_level,
                  original_size, compressed_size, compression_ratio, status

        Raises:
            PluginExecutionError: on compression errors

        """
        source_path = Path(self.config["source_path"])
        output_path = Path(self.config["output_path"])
        format_type = self.config.get("format", "gzip")
        compression_level = self.config.get("compression_level", 6)

        self.logger.info(
            f"Compressing {source_path} to {output_path} using {format_type}"
        )

        try:
            # Validate source path
            if not source_path.exists():
                raise PluginExecutionError(f"Source path does not exist: {source_path}")

            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Perform compression based on format
            if format_type == "gzip":
                result = self._compress_gzip(
                    source_path, output_path, compression_level
                )
            elif format_type == "tar":
                result = self._compress_tar(source_path, output_path, compression_level)
            elif format_type == "zip":
                result = self._compress_zip(source_path, output_path, compression_level)
            else:
                raise PluginExecutionError(
                    f"Unsupported compression format: {format_type}"
                )

            self.logger.info(f"Successfully compressed {source_path} to {output_path}")
            return result

        except PluginExecutionError:
            raise
        except Exception as e:
            error_msg = f"Compression failed for {source_path}: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

    def _compress_gzip(
        self, source_path: Path, output_path: Path, compression_level: int
    ) -> Dict[str, Any]:
        """
        Compress a single file using gzip.
        """
        if source_path.is_dir():
            raise PluginExecutionError(
                "Gzip format only supports single files, not directories"
            )

        with open(source_path, "rb") as f_in:
            with gzip.open(output_path, "wb", compresslevel=compression_level) as f_out:
                shutil.copyfileobj(f_in, f_out)

        return {
            "source_path": str(source_path),
            "output_path": str(output_path),
            "format": "gzip",
            "compression_level": compression_level,
            "original_size": source_path.stat().st_size,
            "compressed_size": output_path.stat().st_size,
            "compression_ratio": output_path.stat().st_size
            / source_path.stat().st_size,
            "status": "success",
        }

    def _compress_tar(
        self, source_path: Path, output_path: Path, compression_level: int
    ) -> Dict[str, Any]:
        """
        Compress files/directories using tar.
        """
        compression = "gz" if output_path.suffix in [".gz", ".tgz"] else ""

        with tarfile.open(
            output_path, f"w:{compression}" if compression else "w"
        ) as tar:
            tar.add(source_path, arcname=source_path.name)

        original_size = self._get_total_size(source_path)
        compressed_size = output_path.stat().st_size

        return {
            "source_path": str(source_path),
            "output_path": str(output_path),
            "format": "tar" + (".gz" if compression else ""),
            "compression_level": compression_level,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compressed_size / original_size,
            "status": "success",
        }

    def _compress_zip(
        self, source_path: Path, output_path: Path, compression_level: int
    ) -> Dict[str, Any]:
        """
        Compress files/directories using zip.
        """
        with zipfile.ZipFile(
            output_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=compression_level,
        ) as zipf:
            if source_path.is_file():
                zipf.write(source_path, source_path.name)
            else:
                for file_path in source_path.rglob("*"):
                    if file_path.is_file():
                        zipf.write(file_path, file_path.relative_to(source_path))

        original_size = self._get_total_size(source_path)
        compressed_size = output_path.stat().st_size

        return {
            "source_path": str(source_path),
            "output_path": str(output_path),
            "format": "zip",
            "compression_level": compression_level,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compressed_size / original_size,
            "status": "success",
        }

    def _get_total_size(self, path: Path) -> int:
        """
        Calculate total size of a file or directory.
        """
        if path.is_file():
            return path.stat().st_size
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
