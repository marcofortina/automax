"""
Step Manager for Automax.

Orchestrates the execution of steps based on YAML configurations. Loads step
configurations dynamically and delegates sub-step execution to SubStepManager.

"""

import importlib
from pathlib import Path
import sys

import yaml

from automax.core.exceptions import AutomaxError
from automax.core.managers.logger_manager import LoggerManager
from automax.core.managers.plugin_manager import PluginManager
from automax.core.managers.substep_manager import SubStepManager
from automax.core.managers.template_manager import TemplateManager
from automax.core.utils.log_utils import print_step_end, print_step_start


class StepManager:
    """
    Manager class for handling step orchestration.

    Loads YAML configurations for each step on-demand and executes them sequentially.
    Supports dry-run mode, pre/post hooks, and error handling.

    """

    def __init__(self, cfg: dict, logger: LoggerManager, plugin_manager: PluginManager):
        """
        Initialize StepManager.

        Args:
            cfg (dict): Loaded configuration dictionary.
            logger (LoggerManager): Logger instance.
            plugin_manager (PluginManager): Plugin manager instance.

        """
        self.cfg = cfg
        self.logger = logger
        self.plugin_manager = plugin_manager
        self.steps_dir = Path(cfg.get("steps_dir", "steps")).resolve()
        self._context = {}  # Global context shared between steps
        self.template_manager = TemplateManager(cfg, self._context)

        # Ensure steps directory parent is in sys.path for dynamic imports
        steps_parent = str(self.steps_dir.parent)
        if steps_parent not in sys.path:
            sys.path.insert(0, steps_parent)
            self.logger.debug(
                f"Added '{steps_parent}' to sys.path for step module imports"
            )

    @property
    def context(self):
        """
        Get the current context.
        """
        return self._context

    @context.setter
    def context(self, value):
        """
        Set the context and update the TemplateManager.
        """
        self._context = value
        self.template_manager.context = value

    def run(
        self, step_ids: list[str] = None, substep_id: str = None, dry_run: bool = False
    ) -> bool:
        """
        Run selected steps or all steps if none specified.

        Args:
            step_ids (list[str], optional): List of step IDs to run.
            substep_id (str, optional): Specific sub-step ID (e.g., '2' for step X.2).
            dry_run (bool): If True, skip actual execution.

        Returns:
            bool: True if all steps completed successfully.

        Raises:
            AutomaxError: On execution errors.

        """
        if not step_ids:
            # If no steps specified, discover all available step YAMLs
            step_ids = sorted(
                [
                    d.stem.replace("step", "")
                    for d in self.steps_dir.iterdir()
                    if d.is_dir() and (d / f"{d.name}.yaml").exists()
                ]
            )

        overall_success = True

        for step_id in step_ids:
            try:
                step_cfg = self._load_step_config(step_id)

                # Render dynamic step configuration
                rendered_step_cfg = self._render_step_config(step_cfg)

                print_step_start(self.logger, step_id, rendered_step_cfg["description"])

                # Optional pre_run hook
                if "pre_run" in rendered_step_cfg:
                    func = self._import_function(rendered_step_cfg["pre_run"])
                    func(self.cfg, self.logger, dry_run)

                # Execute sub-steps
                substep_manager = SubStepManager(
                    self.cfg,
                    self.logger,
                    self.plugin_manager,
                    step_id,
                    rendered_step_cfg["substeps"],
                )

                # Share context between StepManager and SubStepManager
                substep_manager.context = self.context

                substep_success = substep_manager.run(
                    substep_ids=[substep_id] if substep_id else None, dry_run=dry_run
                )
                if not substep_success:
                    overall_success = False

                step_result = "OK" if substep_success else "ERROR"

            except Exception as e:
                self.logger.error(f"Step {step_id} failed: {e}")
                step_result = "ERROR"
                overall_success = False
                raise AutomaxError(f"Failure in step {step_id}: {e}", level="ERROR")
            finally:
                # Optional post_run hook
                if "post_run" in rendered_step_cfg:
                    func = self._import_function(rendered_step_cfg["post_run"])
                    func(self.cfg, self.logger, dry_run, step_result == "OK")
                print_step_end(self.logger, step_id, step_result)

        return overall_success

    def _load_step_config(self, step_id: str) -> dict:
        """
        Load YAML configuration for a specific step.

        Args:
            step_id (str): ID of the step.

        Returns:
            dict: Step configuration.

        Raises:
            AutomaxError: If YAML file not found or invalid.

        """
        yaml_path = (
            Path(self.steps_dir / f"step{step_id}" / f"step{step_id}.yaml")
            .expanduser()
            .resolve()
        )
        if not yaml_path.exists():
            raise AutomaxError(f"Step YAML not found: {yaml_path}", level="FATAL")
        try:
            with open(yaml_path, "r") as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Loaded step configuration from {yaml_path}")
            return config
        except yaml.YAMLError as e:
            raise AutomaxError(f"Invalid YAML in {yaml_path}: {e}", level="FATAL")

    def _render_step_config(self, step_cfg: dict) -> dict:
        """
        Render dynamic step configuration using Jinja2 templates.

        Args:
            step_cfg (dict): Original step configuration.

        Returns:
            dict: Rendered step configuration.

        """
        rendered_cfg = step_cfg.copy()

        # Render step-level fields
        if isinstance(rendered_cfg.get("id"), str) and (
            "{{" in rendered_cfg["id"] or "{%" in rendered_cfg["id"]
        ):
            rendered_cfg["id"] = self.template_manager.render(rendered_cfg["id"])

        if isinstance(rendered_cfg.get("description"), str) and (
            "{{" in rendered_cfg["description"] or "{%" in rendered_cfg["description"]
        ):
            rendered_cfg["description"] = self.template_manager.render(
                rendered_cfg["description"]
            )

        # Render substep configurations
        rendered_substeps = []
        for substep in rendered_cfg.get("substeps", []):
            rendered_substep = self._render_substep_config(substep)
            rendered_substeps.append(rendered_substep)

        rendered_cfg["substeps"] = rendered_substeps

        return rendered_cfg

    def _render_substep_config(self, substep_cfg: dict) -> dict:
        """
        Render dynamic substep configuration using Jinja2 templates.

        Args:
            substep_cfg (dict): Original substep configuration.

        Returns:
            dict: Rendered substep configuration.

        """
        rendered_substep = substep_cfg.copy()

        # Render substep ID and description
        if isinstance(rendered_substep.get("id"), str) and (
            "{{" in rendered_substep["id"] or "{%" in rendered_substep["id"]
        ):
            rendered_substep["id"] = self.template_manager.render(
                rendered_substep["id"]
            )

        if isinstance(rendered_substep.get("description"), str) and (
            "{{" in rendered_substep["description"]
            or "{%" in rendered_substep["description"]
        ):
            rendered_substep["description"] = self.template_manager.render(
                rendered_substep["description"]
            )

        # Render parameters if they contain templates
        if "params" in rendered_substep and isinstance(
            rendered_substep["params"], dict
        ):
            rendered_substep["params"] = self.template_manager.render_dict(
                rendered_substep["params"]
            )

        return rendered_substep

    def _import_function(self, path: str):
        """
        Dynamically import a function from a module path.

        Args:
            path (str): Module.function path.

        Returns:
            callable: The imported function.

        """
        module_name, func_name = path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, func_name)
