"""
Plugin for uncompressing files and archives.
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
class UncompressFilePlugin(BasePlugin):
    """
    Uncompress files and archives.
    """

    METADATA = PluginMetadata(
        name="uncompress_file",
        version="2.0.0",
        description="Uncompress files and archives using gzip, tar, or zip",
        author="Automax Team",
        category="file_operations",
        tags=["uncompress", "extract", "archive", "file", "gzip", "tar", "zip"],
        required_config=["source_path", "output_path"],
        optional_config=["format"],
    )

    SCHEMA = {
        "source_path": {"type": str, "required": True},
        "output_path": {"type": str, "required": True},
        "format": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Uncompress a file or archive.

        Returns:
            Dictionary containing the extraction results.

        Raises:
            PluginExecutionError: If extraction fails.

        """
        source_path = Path(self.config["source_path"])
        output_path = Path(self.config["output_path"])
        format_type = self.config.get("format")

        self.logger.info(
            f"Uncompressing {source_path} to {output_path} using {format_type}"
        )

        try:
            # Validate source file existence
            if not source_path.exists():
                raise PluginExecutionError(f"Source path does not exist: {source_path}")

            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Perform extraction based on format
            if format_type == "gzip":
                result = self._extract_gzip(source_path, output_path)
            elif format_type == "tar":
                result = self._extract_tar(source_path, output_path)
            elif format_type == "zip":
                result = self._extract_zip(source_path, output_path)
            else:
                raise PluginExecutionError(
                    f"Unsupported compression format: {format_type}"
                )

            self.logger.info(
                f"Successfully uncompressed {source_path} to {output_path}"
            )
            return result

        except PluginExecutionError:
            raise

        except Exception as e:
            error_msg = f"Failed to uncompress {source_path} to {output_path}: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

    def _extract_gzip(self, source_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Extract a gzip file.
        """
        with gzip.open(source_path, "rb") as f_in, open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        return {
            "source_path": str(source_path),
            "output_path": str(output_path),
            "format": "gzip",
            "compressed_size": source_path.stat().st_size,
            "extracted_size": output_path.stat().st_size,
            "status": "success",
        }

    def _extract_tar(self, source_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Extract a tar archive.
        """
        with tarfile.open(source_path, "r") as tar:
            tar.extractall(output_path)

        return {
            "source_path": str(source_path),
            "output_path": str(output_path),
            "format": "tar",
            "status": "success",
        }

    def _extract_zip(self, source_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Extract a zip archive.
        """
        with zipfile.ZipFile(source_path, "r") as zipf:
            zipf.extractall(output_path)

        return {
            "source_path": str(source_path),
            "output_path": str(output_path),
            "format": "zip",
            "compressed_size": source_path.stat().st_size,
            "extracted_size": output_path.stat().st_size,
            "status": "success",
        }
