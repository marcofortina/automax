"""
Plugin for executing commands on remote servers via SSH.
"""

from typing import Any, Dict

import paramiko

from automax.plugins import BasePlugin, PluginMetadata, register_plugin
from automax.plugins.exceptions import PluginExecutionError


@register_plugin
class SSHCommandPlugin(BasePlugin):
    """
    Execute commands on remote servers via SSH.
    """

    METADATA = PluginMetadata(
        name="ssh_command",
        version="2.0.0",
        description="Execute commands on remote servers via SSH",
        author="Automax Team",
        category="system",
        tags=["ssh", "remote", "command", "execute"],
        required_config=["host", "command"],
        optional_config=["port", "username", "password", "key_file", "timeout"],
    )

    SCHEMA = {
        "host": {"type": str, "required": True},
        "command": {"type": str, "required": True},
        "username": {"type": str, "required": False},
        "key_file": {"type": str, "required": False},
        "password": {"type": str, "required": False},
        "port": {"type": int, "required": False},
        "timeout": {"type": (int, float), "required": False},
    }

    def execute(self) -> Dict[str, Any]:
        """
        Execute a command on remote server via SSH.

        Returns:
            Dictionary containing command execution results.

        Raises:
            PluginExecutionError: If SSH connection or command execution fails.

        """
        host = self.config["host"]
        command = self.config["command"]
        port = self.config.get("port", 22)
        username = self.config.get("username", "root")
        password = self.config.get("password")
        key_file = self.config.get("key_file")
        timeout = self.config.get("timeout", 30)

        self.logger.info(f"Executing SSH command on {host}:{port}: {command}")
        self.logger.debug(f"SSH COMMAND on {host}:{port}: {command}")

        ssh_client = None
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to SSH server
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": timeout,
            }

            if password:
                connect_kwargs["password"] = password
            elif key_file:
                connect_kwargs["key_filename"] = key_file

            ssh_client.connect(**connect_kwargs)
            self.logger.debug(f"SSH connection established to {host}:{port}")

            # Execute command
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            stdout_output = stdout.read().decode("utf-8").strip()
            stderr_output = stderr.read().decode("utf-8").strip()

            if stdout_output:
                self.logger.debug(f"SSH command output on {host}:\n{stdout_output}")
            if stderr_output:
                self.logger.debug(
                    f"SSH command error output on {host}:\n{stderr_output}"
                )

            result = {
                "host": host,
                "port": port,
                "command": command,
                "exit_code": exit_code,
                "stdout": stdout_output,
                "stderr": stderr_output,
                "status": "success" if exit_code == 0 else "failure",
            }

            if exit_code != 0:
                self.logger.warning(
                    f"SSH command exited with code {exit_code} on {host}: {command}"
                )
            else:
                self.logger.info(
                    f"SSH command executed successfully on {host}: {command}"
                )

            return result

        except paramiko.AuthenticationException as e:
            error_msg = f"SSH authentication failed for {username}@{host}:{port}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
        except paramiko.SSHException as e:
            error_msg = f"SSH error connecting to {host}:{port}: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to execute SSH command on {host}:{port}: {e}"
            self.logger.error(error_msg)
            raise PluginExecutionError(error_msg) from e
        finally:
            if ssh_client:
                ssh_client.close()
                self.logger.debug(f"SSH connection closed to {host}:{port}")
