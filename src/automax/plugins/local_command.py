"""
Plugin for executing local system commands.
"""

import subprocess
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class LocalCommandPlugin(BasePlugin):
    """
    Execute local system commands and return output.
    """

    METADATA = PluginMetadata(
        name="local_command",
        version="2.0.0",
        description="Execute local system commands with output capture",
        author="Marco Fortina",
        category="system",
        tags=["command", "local", "system", "execute"],
        required_config=["command"],
        optional_config=["timeout", "shell", "cwd", "env", "input_data"],
    )

    SCHEMA = {
        "command": {"type": str, "required": True},
        "timeout": {"type": (int, float), "required": False},
        "shell": {"type": bool, "required": False},
        "cwd": {"type": str, "required": False},
        "env": {"type": dict, "required": False},
        "input_data": {"type": str, "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute a local system command.

        Returns:
            Dictionary containing:
                - command (str): The command that was executed
                - returncode (int): The return code of the command
                - stdout (str): The standard output of the command
                - stderr (str): The standard error of the command
                - timeout (int/float): The timeout value used
                - shell (bool): Whether shell mode was used
                - status (str): "success" if returncode is 0, "failure" otherwise

        Raises:
            PluginExecutionError: If command execution fails, times out,
                                or command is not found.

        """
        command = self.config["command"]
        timeout = self.config.get("timeout", 30)
        shell = self.config.get("shell", True)
        cwd = self.config.get("cwd")
        env = self.config.get("env")
        input_data = self.config.get("input_data")

        self.logger.info(f"Executing local command: {command}")

        try:
            result = subprocess.run(
                command,
                shell=shell,
                timeout=timeout,
                cwd=cwd,
                env=env,
                input=input_data,
                capture_output=True,
                text=True,
                encoding="utf-8" if input_data else None,
            )

            if result.stdout and result.stdout.strip():
                self.logger.debug(f"Command output:\n{result.stdout}")
            if result.stderr and result.stderr.strip():
                self.logger.debug(f"Command error output:\n{result.stderr}")

            status = "success" if result.returncode == 0 else "failure"

            if status == "failure":
                self.logger.warning(
                    f"Command exited with non-zero code {result.returncode}: {command}"
                )
            else:
                self.logger.info(f"Command executed successfully: {command}")

            return {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timeout": timeout,
                "shell": shell,
                "status": status,
            }

        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {timeout} seconds: {command}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

        except FileNotFoundError as e:
            error_msg = f"Command not found: {command}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to execute command: {command} - {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
