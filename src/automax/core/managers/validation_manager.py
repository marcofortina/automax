"""
Validation Manager for Automa.

Validates YAML configurations, CLI arguments, and plugin parameters against schemas.
Uses jsonschema for YAML structure validation.
"""

from pathlib import Path

import jsonschema
import yaml

from automax.core.exceptions import AutomaError


class ValidationManager:
    """
    Manager class for validating configurations and arguments.

    Ensures YAML files conform to schema, plugin parameters are valid,
    and CLI arguments reference existing steps.
    """

    STEP_SCHEMA = {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "pre_run": {"type": "string"},
            "post_run": {"type": "string"},
            "substeps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": "string"},
                        "plugin": {"type": "string"},
                        "retry": {"type": "integer"},
                        "params": {"type": "object"},
                        "output_key": {"type": "string"},
                    },
                    "required": ["id", "description", "plugin", "params"],
                },
            },
        },
        "required": ["description", "substeps"],
    }

    def __init__(self, cfg: dict, plugin_manager, steps_dir: Path):
        """
        Initialize ValidationManager.

        Args:
            cfg (dict): Configuration dictionary.
            plugin_manager: Plugin manager instance.
            steps_dir (Path): Directory for step YAML files.
        """
        self.cfg = cfg
        self.plugin_manager = plugin_manager
        self.steps_dir = steps_dir

    def validate_step_yaml(self, step_id: str):
        """
        Validate the YAML for a specific step.

        Checks structure with jsonschema, plugin params against SCHEMA,
        and resolves placeholders for validation.

        Args:
            step_id (str): Step ID.

        Raises:
            AutomaError: On validation failures.
        """
        yaml_path = self.steps_dir / f"step{step_id}" / f"step{step_id}.yaml"
        if not yaml_path.exists():
            raise AutomaError(f"Step YAML not found: {yaml_path}", level="FATAL")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        # Validate overall schema
        try:
            jsonschema.validate(instance=data, schema=self.STEP_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise AutomaError(
                f"YAML schema validation failed for {yaml_path}: {e}", level="FATAL"
            )

        # Validate each sub-step
        for sub in data["substeps"]:
            plugin_name = sub["plugin"]
            if plugin_name not in self.plugin_manager.registry:
                raise AutomaError(
                    f"Unknown plugin '{plugin_name}' in sub-step {step_id}.{sub['id']}",
                    level="FATAL",
                )

            schema = self.plugin_manager.get_schema(plugin_name)
            params = sub["params"]
            self._validate_params(params, schema)

            # Check for sensitive params (warn if hard-coded)
            sensitive_keys = ["password", "key_path"]  # Expand as needed
            for key in sensitive_keys:
                if (
                    key in params
                    and isinstance(params[key], str)
                    and not params[key].startswith("{")
                    and not params[key].startswith("$")
                ):
                    self.plugin_manager.logger.warning(
                        f"Potential hard-coded sensitive param '{key}' in sub-step {step_id}.{sub['id']}. Consider using env vars."
                    )

            # Validate placeholder resolution
            for k, v in params.items():
                if isinstance(v, str) and "{" in v:
                    try:
                        v.format(**self.cfg)
                    except KeyError as e:
                        raise AutomaError(
                            f"Missing config key for placeholder in {k}: {e}",
                            level="ERROR",
                        )

    def validate_cli_args(self, execution_plan: dict):
        """
        Validate CLI arguments against available steps.

        Args:
            execution_plan (dict): Parsed step/sub-step plan from CLI.

        Raises:
            AutomaError: If invalid steps/sub-steps.
        """
        for step_id in execution_plan:
            yaml_path = self.steps_dir / f"step{step_id}" / f"step{step_id}.yaml"
            if not yaml_path.exists():
                raise AutomaError(
                    f"Invalid step ID {step_id}: YAML not found", level="FATAL"
                )

    def _validate_params(self, params: dict, schema: dict):
        """
        Validate parameters against plugin SCHEMA.

        Args:
            params (dict): Sub-step parameters.
            schema (dict): Plugin schema.

        Raises:
            AutomaError: On param validation failures.
        """
        for key, spec in schema.items():
            if spec.get("required") and key not in params:
                raise AutomaError(f"Missing required param '{key}'", level="ERROR")
            if key in params:
                expected_type = spec["type"]
                if not isinstance(params[key], expected_type):
                    raise AutomaError(
                        f"Invalid type for '{key}': expected {expected_type}, got {type(params[key])}",
                        level="ERROR",
                    )
