"""
Sub-Step Manager for Automax.

Handles the execution of sub-steps within a step, including parameter resolution, plugin
invocation, retries, and output context management.

"""

import importlib
import os
import re

from automax.core.exceptions import AutomaxError
from automax.core.managers.template_manager import TemplateManager
from automax.core.utils.data_transformer import DataTransformer
from automax.core.utils.log_utils import print_substep_end, print_substep_start


class SubStepManager:
    """
    Manager class for executing sub-steps.

    Resolves placeholders and environment variables in parameters, invokes plugins with
    retries, and manages output context.

    """

    def __init__(
        self,
        cfg: dict,
        logger,
        plugin_manager,
        step_id: str,
        substeps_cfg: list[dict],
        pre_run: str = None,
        post_run: str = None,
    ):
        """
        Initialize SubStepManager.

        Args:
            cfg (dict): Configuration dictionary.
            logger: Logger instance.
            plugin_manager: Plugin manager instance.
            step_id (str): Current step ID.
            substeps_cfg (list[dict]): List of sub-step configurations from YAML.
            pre_run (str, optional): Pre-run hook function path.
            post_run (str, optional): Post-run hook function path.

        """
        self.cfg = cfg
        self.logger = logger
        self.plugin_manager = plugin_manager
        self.step_id = step_id
        self.substeps_cfg = substeps_cfg
        self._context = {}  # Shared context for output between sub-steps
        self.pre_run = pre_run
        self.post_run = post_run
        self.template_manager = TemplateManager(cfg, self._context)

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

    def run(self, substep_ids: list[str] = None, dry_run: bool = False) -> bool:
        """
        Run specified sub-steps or all if none provided.

        Args:
            substep_ids (list[str], optional): Specific sub-step IDs.
            dry_run (bool): If True, skip execution.

        Returns:
            bool: True if all sub-steps succeeded.

        Raises:
            AutomaxError: On sub-step errors.

        """
        # Execute pre-run hook if defined
        if self.pre_run and not dry_run:
            self._execute_hook(self.pre_run, "pre_run")

        if not substep_ids:
            substep_ids = [sub["id"] for sub in self.substeps_cfg]

        success = True
        for sub_id in substep_ids:
            sub_cfg = next((s for s in self.substeps_cfg if s["id"] == sub_id), None)
            if not sub_cfg:
                raise AutomaxError(
                    f"Sub-step {self.step_id}.{sub_id} not found", level="ERROR"
                )

            print_substep_start(
                self.logger, self.step_id, sub_id, sub_cfg["description"]
            )

            try:
                # Resolve parameters
                params = self._resolve_params(sub_cfg["params"])

                if dry_run:
                    self.logger.info(
                        f"[DRY-RUN] Sub-step {self.step_id}.{sub_id} skipped"
                    )
                    result = "OK"
                else:
                    # Invoke plugin with retries
                    retry_count = sub_cfg.get("retry", 0)
                    for attempt in range(retry_count + 1):
                        try:
                            plugin_class = self.plugin_manager.get_plugin(
                                sub_cfg["plugin"]
                            )
                            plugin_instance = plugin_class(params)
                            plugin_instance.logger = self.logger
                            output = plugin_instance.execute()
                            break
                        except Exception as e:
                            if attempt == retry_count:
                                raise
                            self.logger.warning(
                                f"Retry {attempt+1}/{retry_count+1} for sub-step {self.step_id}.{sub_id}: {e}"
                            )

                    # Save output to context if specified
                    if "output_key" in sub_cfg and output is not None:
                        self.context[sub_cfg["output_key"]] = output

                    # Apply advanced output mapping if specified
                    if "output_mapping" in sub_cfg and output is not None:
                        self._apply_output_mapping(
                            output, sub_cfg["output_mapping"], sub_id
                        )

                    result = "OK"

            except Exception as e:
                self.logger.error(f"Sub-step {self.step_id}.{sub_id} failed: {e}")
                result = "ERROR"
                success = False
                raise AutomaxError(
                    f"Error in sub-step {self.step_id}.{sub_id}: {e}", level="ERROR"
                )
            finally:
                print_substep_end(self.logger, self.step_id, sub_id, result)

        # Execute post-run hook if defined
        if self.post_run and not dry_run:
            self._execute_hook(self.post_run, "post_run")

        return success

    def _apply_output_mapping(
        self, result: any, output_mapping: dict, substep_id: str
    ) -> None:
        """
        Apply advanced output mapping to transform and store result data.

        Args:
            result: Plugin execution result
            output_mapping: Output mapping configuration
            substep_id: Sub-step identifier for logging

        Raises:
            AutomaxError: If output mapping fails

        """
        try:
            target_key = output_mapping["target"]
            # Use DataTransformer with template manager
            data_transformer = DataTransformer(self.template_manager)
            transformed_data = data_transformer.transform(result, output_mapping)

            self.context[target_key] = transformed_data
            self.logger.debug(
                f"Applied output mapping for sub-step {substep_id}, "
                f"stored transformed data in context under key: {target_key}"
            )

        except Exception as e:
            error_msg = f"Failed to apply output mapping for sub-step {substep_id}: {e}"
            self.logger.error(error_msg)
            raise AutomaxError(error_msg, level="ERROR")

    def _resolve_legacy_placeholders(self, value: str) -> str:
        """
        Resolve legacy placeholder patterns for backward compatibility.

        Supports:
        - {key} for configuration and context values
        - $VAR and ${VAR} for environment variables

        Args:
            value: String with legacy placeholders

        Returns:
            String with resolved placeholders

        Raises:
            AutomaxError: If any placeholder key is missing

        """
        # Resolve {key} placeholders from config and context
        for key in self.cfg:
            placeholder = f"{{{key}}}"
            if placeholder in value:
                value = value.replace(placeholder, str(self.cfg[key]))

        for key in self.context:
            placeholder = f"{{{key}}}"
            if placeholder in value:
                value = value.replace(placeholder, str(self.context[key]))

        # Check for any remaining {key} placeholders
        remaining_placeholders = re.findall(r"\{[^}]+\}", value)
        if remaining_placeholders:
            raise AutomaxError(
                f"Missing placeholder key: {remaining_placeholders[0][1:-1]}"
            )

        # Resolve environment variables
        value = os.path.expandvars(value)

        return value

    def _resolve_params(self, params: dict) -> dict:
        """
        Resolve placeholders and environment variables in parameters.

        Supports both Jinja2 templates and legacy placeholders for backward compatibility.

        Args:
            params (dict): Original parameters.

        Returns:
            dict: Resolved parameters.

        """
        resolved = {}
        template_fields = []

        # First pass: identify template fields
        for k, v in params.items():
            if k.endswith("_is_template") and v is True:
                field_name = k[:-12]  # Remove '_is_template' suffix
                template_fields.append(field_name)

        # Second pass: resolve values
        for k, v in params.items():
            # Skip template flags
            if k.endswith("_is_template"):
                continue

            if isinstance(v, str):
                try:
                    # Check if this field should be treated as template
                    is_template = k in template_fields or "{{" in v or "{%" in v

                    if is_template:
                        v = self.template_manager.render(v)
                    else:
                        # Otherwise, use legacy resolution
                        v = self._resolve_legacy_placeholders(v)
                except Exception as e:
                    raise AutomaxError(
                        f"Failed to resolve parameter '{k}': {str(e)}", level="ERROR"
                    )
            resolved[k] = v
        return resolved

    def _execute_hook(self, hook_path: str, hook_type: str):
        """
        Execute a hook function.

        Args:
            hook_path: Dot-separated path to hook function
            hook_type: Type of hook for logging

        Raises:
            AutomaxError: If hook execution fails

        """
        try:
            module_name, function_name = hook_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            hook_function = getattr(module, function_name)

            # Call hook function with context
            hook_function(logger=self.logger, step_id=self.step_id)

            self.logger.info("Executed %s hook: %s", hook_type, hook_path)

        except Exception as e:
            error_msg = f"Failed to execute {hook_type} hook {hook_path}: {e}"
            self.logger.error(error_msg)
            raise AutomaxError(error_msg, level="ERROR")
