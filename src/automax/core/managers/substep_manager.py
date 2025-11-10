"""
Sub-Step Manager for Automa.

Handles the execution of sub-steps within a step, including parameter resolution,
plugin invocation, retries, and output context management.
"""

import os

from automax.core.exceptions import AutomaxError
from automax.core.utils.log_utils import print_substep_end, print_substep_start


class SubStepManager:
    """
    Manager class for executing sub-steps.

    Resolves placeholders and environment variables in parameters,
    invokes plugins with retries, and manages output context.
    """

    def __init__(
        self, cfg: dict, logger, plugin_manager, step_id: str, substeps_cfg: list[dict]
    ):
        """
        Initialize SubStepManager.

        Args:
            cfg (dict): Configuration dictionary.
            logger: Logger instance.
            plugin_manager: Plugin manager instance.
            step_id (str): Current step ID.
            substeps_cfg (list[dict]): List of sub-step configurations from YAML.
        """
        self.cfg = cfg
        self.logger = logger
        self.plugin_manager = plugin_manager
        self.step_id = step_id
        self.substeps_cfg = substeps_cfg
        self.context = {}  # Shared context for output between sub-steps

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
                if dry_run:
                    self.logger.info(
                        f"[DRY-RUN] Sub-step {self.step_id}.{sub_id} skipped"
                    )
                    result = "OK"
                else:
                    # Resolve parameters
                    params = self._resolve_params(sub_cfg["params"])

                    # Invoke plugin with retries
                    retry_count = sub_cfg.get("retry", 0)
                    for attempt in range(retry_count + 1):
                        try:
                            utility = self.plugin_manager.get_plugin(sub_cfg["plugin"])
                            output = utility(
                                **params, logger=self.logger, dry_run=dry_run
                            )
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

        return success

    def _resolve_params(self, params: dict) -> dict:
        """
        Resolve placeholders and environment variables in parameters.

        Supports {config_key} from cfg and $ENV_VAR from os.environ.

        Args:
            params (dict): Original parameters.

        Returns:
            dict: Resolved parameters.
        """
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str):
                # Resolve config placeholders
                try:
                    v = v.format(**self.cfg, **self.context)
                except KeyError as e:
                    raise AutomaxError(f"Missing placeholder key: {e}", level="ERROR")
                # Resolve env vars (e.g., $HOME)
                v = os.path.expandvars(v)
            resolved[k] = v
        return resolved
