"""
Read File Content Plugin for Automax.

This plugin reads content from files and returns it as string.

"""

from pathlib import Path
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class ReadFileContentPlugin(BasePlugin):
    """
    Plugin for reading content from files.

    This plugin supports multiple encodings and provides error handling for file
    operations.

    """

    METADATA = PluginMetadata(
        name="read_file_content",
        version="2.0.0",
        description="Read content from files with encoding support",
        author="Automax Team",
        category="file_operations",
        tags=["file", "read", "content"],
        required_config=["file_path"],
        optional_config=["encoding"],
    )

    SCHEMA = {
        "file_path": {"type": str, "required": True},
        "encoding": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Read content from specified file.

        Returns:
            Dictionary containing file content and metadata

        Raises:
            PluginExecutionError: If file cannot be read

        """
        file_path = Path(self.config["file_path"])
        encoding = self.config.get("encoding", "utf-8")

        self.logger.info(f"Reading file: {file_path}")

        try:
            if not file_path.exists():
                raise PluginExecutionError(f"File not found: {file_path}")

            if not file_path.is_file():
                raise PluginExecutionError(f"Path is not a file: {file_path}")

            content = file_path.read_text(encoding=encoding)
            self.logger.info(f"Read {len(content)} bytes from {file_path}")

            return {
                "file_path": str(file_path),
                "content": content,
                "encoding": encoding,
                "size": len(content),
                "status": "success",
            }

        except UnicodeDecodeError as e:
            raise PluginExecutionError(
                f"Encoding error reading {file_path}: {e}"
            ) from e

        except IOError as e:
            raise PluginExecutionError(f"IO error reading {file_path}: {e}") from e
