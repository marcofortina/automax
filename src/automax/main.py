"""
Core orchestrator for Automax.

Contains the main execution logic and can be used programmatically:
    from automax import run_automax
    run_automax(steps=["1", "2"], dry_run=True)

"""

from pathlib import Path
import time
from typing import List

from automax.core.managers.config_manager import ConfigManager
from automax.core.managers.logger_manager import LoggerManager
from automax.core.managers.plugin_manager import PluginManager
from automax.core.managers.step_manager import StepManager
from automax.core.managers.validation_manager import ValidationManager
from automax.core.utils.log_utils import print_main_result


def _parse_execution_plan(steps: List[str]) -> dict:
    """
    Convert CLI step strings into execution plan dictionary.
    """
    plan = {}
    for arg in steps:
        if ":" in arg:
            step, subs = arg.split(":")
            plan[step] = subs.split(",") if subs else []
        else:
            plan[arg] = None
    return plan


def run_automax(
    steps: List[str] = None,
    config_path: str = "examples/config/config.yaml",
    dry_run: bool = False,
    json_log: bool = False,
    list_only: bool = False,
    validate_only: bool = False,
) -> int:
    """
    Programmatic entry point for Automa execution.

    Returns:
        int: Exit code (0 = success).

    """
    steps = steps or []

    start_time = time.time()

    # Load configuration
    config_mgr = ConfigManager(config_path)
    cfg = config_mgr.cfg

    # Override from args
    if json_log:
        cfg["json_log"] = True

    # Initialize core components
    logger = LoggerManager(
        log_directory=cfg["log_dir"],
        log_level=cfg.get("log_level", "DEBUG"),
        json_log=cfg.get("json_log", False),
    )

    plugin_mgr = PluginManager(logger=logger)
    plugin_mgr.load_plugins()

    validator = ValidationManager(cfg, plugin_mgr, Path(cfg["steps_dir"]))

    execution_plan = _parse_execution_plan(steps)

    # Validation phase
    try:
        validator.validate_cli_args(execution_plan)
        for step_id in execution_plan:
            validator.validate_step_yaml(step_id)
        logger.info("Validation successful")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1

    if validate_only:
        logger.info("Validate-only mode: Exiting after successful validation")
        return 0

    if list_only:
        available = sorted(
            [
                d.stem.replace("step", "")
                for d in Path(cfg["steps_dir"]).iterdir()
                if d.is_dir() and (d / f"{d.name}.yaml").exists()
            ]
        )
        print("Available steps:", " ".join(available))
        return 0

    # Execution
    step_mgr = StepManager(cfg, logger, plugin_mgr)
    rc = 0
    fatal = False

    try:
        for step_id, substeps in execution_plan.items():
            if fatal:
                break
            success = step_mgr.run(
                step_ids=[step_id],
                substep_id=substeps[0] if substeps else None,
                dry_run=dry_run,
            )
            if not success:
                rc = 1
    except KeyboardInterrupt:
        logger.fatal("Execution interrupted by user.")
        rc = 1
    except Exception as e:
        logger.fatal(f"Unexpected error: {e}")
        rc = 1

    elapsed = time.time() - start_time
    print_main_result(logger, rc, elapsed)
    return rc
