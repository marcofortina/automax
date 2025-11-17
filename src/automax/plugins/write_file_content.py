"""
Write File Content Plugin for Automax.

This plugin writes content to files with support for different encodings and modes.

"""

from pathlib import Path
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class WriteFileContentPlugin(BasePlugin):
    """
    Plugin for writing content to files.

    This plugin supports different file modes and encodings, with optional directory
    creation.

    """

    METADATA = PluginMetadata(
        name="write_file_content",
        version="2.0.0",
        description="Write content to files with encoding and mode support",
        author="Automax Team",
        category="file_operations",
        tags=["file", "write", "content"],
        required_config=["file_path", "content"],
        optional_config=["encoding", "mode", "create_dirs"],
    )

    SCHEMA = {
        "file_path": {"type": str, "required": True},
        "content": {"type": str, "required": True},
        "create_dirs": {"type": bool, "required": False},
        "encoding": {"type": str, "required": False},
        "mode": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Write content to specified file.

        Returns:
            Dictionary containing operation results

        Raises:
            PluginExecutionError: If file cannot be written

        """
        file_path = Path(self.config["file_path"])
        content = self.config["content"]
        encoding = self.config.get("encoding", "utf-8")
        mode = self.config.get("mode", "w")
        create_dirs = self.config.get("create_dirs", False)

        self.logger.info(f"Writing content to file: {file_path}")

        try:
            # Create directories if needed
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directories for: {file_path}")

            # Validate write mode
            if mode not in ["w", "a", "x"]:
                raise PluginExecutionError(f"Invalid file mode: {mode}")

            # Write content to file
            with open(file_path, mode, encoding=encoding) as file:
                file.write(content)

            # Verify file was created and get stats
            if file_path.exists():
                file_size = file_path.stat().st_size
            else:
                raise PluginExecutionError(f"File was not created: {file_path}")

            result = {
                "file_path": str(file_path),
                "content_length": len(content),
                "file_size": file_size,
                "encoding": encoding,
                "mode": mode,
                "create_dirs": create_dirs,
                "status": "success",
            }

            self.logger.info(f"Successfully wrote {len(content)} bytes to {file_path}")
            return result

        except PermissionError as e:
            raise PluginExecutionError(
                f"Permission denied writing to {file_path}: {e}"
            ) from e

        except IOError as e:
            raise PluginExecutionError(f"IO error writing to {file_path}: {e}") from e

        except Exception as e:
            raise PluginExecutionError(
                f"Unexpected error writing to {file_path}: {e}"
            ) from e
