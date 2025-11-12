"""
Utility functions for logging banners and results in Automax.
"""

from datetime import timedelta


def print_step_start(logger, step_id, description):
    """
    Print and log the start banner for a step.

    Args:
        logger: LoggerManager instance.
        step_id (str): Step ID.
        description (str): Step description.

    """
    banner = f"""
**************************************************************************
  ACTION RUNNING:
  STEP   : [{step_id}] {description}
**************************************************************************
"""
    logger.info(banner)


def print_step_end(logger, step_id, result):
    """
    Print and log the end banner for a step.

    Args:
        logger: LoggerManager instance.
        step_id (str): Step ID.
        result (str): Result status (e.g., "OK" or "ERROR").

    """
    banner = f"""
==========================================================================
  STEP   : [{step_id}] - RESULT : {result}
==========================================================================
"""
    logger.info(banner)


def print_substep_start(logger, step_id, substep_id, description):
    """
    Print and log the start banner for a sub-step.

    Args:
        logger: LoggerManager instance.
        step_id (str): Step ID.
        substep_id (str): Sub-step ID.
        description (str): Sub-step description.

    """
    banner = f"""
--------------------------------------------------------------------------
## STEP {step_id}:{substep_id} - {description}
--------------------------------------------------------------------------
"""
    logger.info(banner)


def print_substep_end(logger, step_id, substep_id, result):
    """
    Print and log the end banner for a sub-step.

    Args:
        logger: LoggerManager instance.
        step_id (str): Step ID.
        substep_id (str): Sub-step ID.
        result (str): Result status (e.g., "OK" or "ERROR").

    """
    banner = f"""
--------------------------------------------------------------------------
## STEP {step_id}:{substep_id} - Result: {result}
--------------------------------------------------------------------------
"""
    logger.info(banner)


def print_main_result(logger, rc, elapsed=None):
    """
    Print and log the global result with return code and optional elapsed time.

    Args:
        logger: LoggerManager instance.
        rc (int): Return code (0 for success, 1 for failure).
        elapsed (float, optional): Total execution time in seconds.

    """
    status = "SUCCESS" if rc == 0 else "FAILURE"
    banner = f"""
**************************************************************************
GLOBAL RESULT: {status} (RC: {rc})
"""
    if elapsed is not None:
        elapsed_str = str(timedelta(seconds=elapsed))
        banner += f"Total Elapsed Time: {elapsed_str}\n"
    banner += (
        "**************************************************************************\n"
    )
    logger.info(banner)
