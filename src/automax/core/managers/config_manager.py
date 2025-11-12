"""
Configuration manager for Automax.

Responsible for loading, validating, and providing access to configuration.

"""

import os
from pathlib import Path

import yaml

from automax.core.exceptions import AutomaxError


class ConfigManager:
    """
    Manager class for Automax configuration.

    Provides methods to load, validate, and access configuration data.

    """

    REQUIRED_SSH_FIELDS = ["private_key", "timeout"]
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]

    def __init__(self, config_file=None):
        """
        Initialize ConfigManager.

        Args:
            config_file (str or dict, optional): Path to YAML config or preloaded dict.

        """
        self._cfg = None
        if config_file:
            self.load(config_file)

    @property
    def cfg(self):
        """
        Return the loaded configuration dictionary.
        """
        if self._cfg is None:
            raise AutomaxError("Configuration has not been loaded yet", level="FATAL")
        return self._cfg

    def load(self, config_file):
        """
        Load YAML configuration and validate required fields.

        Args:
            config_file (str or dict): Path to YAML config or a dict already loaded

        Raises:
            FileNotFoundError: If config file does not exist
            AutomaxError: If invalid YAML syntax or required fields are missing, with level 'FATAL'

        """
        if isinstance(config_file, dict):
            cfg = config_file
        else:
            path = Path(config_file).expanduser().resolve()
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_file}")
            with open(config_file, "r") as f:
                try:
                    cfg = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise AutomaxError(
                        f"Invalid YAML syntax in config file: {e}", level="FATAL"
                    )

        if cfg is None:
            raise AutomaxError("Empty or invalid configuration file", level="FATAL")

        self._cfg = cfg
        self._validate()

    def _validate(self):
        """
        Run all validation checks on the loaded configuration.
        """
        cfg = self._cfg

        # Validate SSH section
        for field in self.REQUIRED_SSH_FIELDS:
            if field not in cfg.get("ssh", {}):
                raise AutomaxError(
                    f"Missing required SSH configuration: {field}", level="FATAL"
                )

        # Validate log_dir
        if "log_dir" not in cfg:
            raise AutomaxError("Missing required configuration: log_dir", level="FATAL")

        private_key_path = Path(cfg["ssh"]["private_key"]).expanduser().resolve()
        if not private_key_path.exists():
            raise AutomaxError(
                f"SSH private key does not exist: {private_key_path}", level="FATAL"
            )
        if not private_key_path.is_file():
            raise AutomaxError(
                f"SSH private key is not a file: {private_key_path}", level="FATAL"
            )
        if not os.access(private_key_path, os.R_OK):
            raise AutomaxError(
                f"SSH private key is not readable: {private_key_path}", level="FATAL"
            )

        if not isinstance(cfg["ssh"]["timeout"], int) or cfg["ssh"]["timeout"] <= 0:
            raise AutomaxError("SSH timeout must be a positive integer", level="FATAL")

        log_dir = Path(cfg["log_dir"]).expanduser().resolve()
        if not log_dir.exists():
            raise AutomaxError(
                f"Log directory does not exist: {log_dir}", level="FATAL"
            )
        if not log_dir.is_dir():
            raise AutomaxError(
                f"Log directory is not a directory: {log_dir}", level="FATAL"
            )
        if not os.access(log_dir, os.W_OK):
            raise AutomaxError(
                f"Log directory is not writable: {log_dir}", level="FATAL"
            )

        if "log_level" in cfg and cfg["log_level"].upper() not in self.VALID_LOG_LEVELS:
            raise AutomaxError(
                f"Invalid log_level: {cfg['log_level']}. Must be DEBUG, INFO, WARN, or ERROR.",
                level="FATAL",
            )

        if "json_log" in cfg and not isinstance(cfg["json_log"], bool):
            raise AutomaxError("json_log must be a boolean value", level="FATAL")

        if "temp_dir" in cfg:
            temp_dir = Path(cfg["temp_dir"])
            if not temp_dir.exists() or not temp_dir.is_dir():
                raise AutomaxError(
                    f"Invalid temp_dir: {temp_dir} (must exist and be a directory)",
                    level="FATAL",
                )
            if not os.access(temp_dir, os.R_OK | os.W_OK):
                raise AutomaxError(
                    f"temp_dir is not readable/writable: {temp_dir}", level="FATAL"
                )
