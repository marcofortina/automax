"""
Tests for step pre-run and post-run hooks functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.substep_manager import SubStepManager


class TestStepHooks:
    """
    Test pre-run and post-run hooks in steps.
    """

    def test_pre_run_hook_execution(self):
        """
        Verify pre-run hook is executed before substeps.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_id = "1"
        substeps_cfg = []
        pre_run = "tests.mocks.hooks.pre_run"

        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module
            mock_hook = MagicMock()
            mock_module.pre_run = mock_hook

            manager = SubStepManager(
                cfg={},
                logger=mock_logger,
                plugin_manager=mock_plugin_manager,
                step_id=step_id,
                substeps_cfg=substeps_cfg,
                pre_run=pre_run,
            )

            manager.run(dry_run=False)
            mock_hook.assert_called_once_with(logger=mock_logger, step_id=step_id)

    def test_post_run_hook_execution(self):
        """
        Verify post-run hook is executed after substeps.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_id = "1"
        substeps_cfg = []
        post_run = "tests.mocks.hooks.post_run"

        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module
            mock_hook = MagicMock()
            mock_module.post_run = mock_hook

            manager = SubStepManager(
                cfg={},
                logger=mock_logger,
                plugin_manager=mock_plugin_manager,
                step_id=step_id,
                substeps_cfg=substeps_cfg,
                post_run=post_run,
            )

            manager.run(dry_run=False)
            mock_hook.assert_called_once_with(logger=mock_logger, step_id=step_id)

    def test_both_hooks_execution(self):
        """
        Verify both pre-run and post-run hooks are executed.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_id = "1"
        substeps_cfg = []
        pre_run = "tests.mocks.hooks.pre_run"
        post_run = "tests.mocks.hooks.post_run"

        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module
            mock_pre_hook = MagicMock()
            mock_post_hook = MagicMock()
            mock_module.pre_run = mock_pre_hook
            mock_module.post_run = mock_post_hook

            manager = SubStepManager(
                cfg={},
                logger=mock_logger,
                plugin_manager=mock_plugin_manager,
                step_id=step_id,
                substeps_cfg=substeps_cfg,
                pre_run=pre_run,
                post_run=post_run,
            )

            manager.run(dry_run=False)
            mock_pre_hook.assert_called_once_with(logger=mock_logger, step_id=step_id)
            mock_post_hook.assert_called_once_with(logger=mock_logger, step_id=step_id)

    def test_hooks_skipped_in_dry_run(self):
        """
        Verify hooks are not executed in dry-run mode.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_id = "1"
        substeps_cfg = []
        pre_run = "tests.mocks.hooks.pre_run"
        post_run = "tests.mocks.hooks.post_run"

        with patch("importlib.import_module") as mock_import:
            manager = SubStepManager(
                cfg={},
                logger=mock_logger,
                plugin_manager=mock_plugin_manager,
                step_id=step_id,
                substeps_cfg=substeps_cfg,
                pre_run=pre_run,
                post_run=post_run,
            )

            manager.run(dry_run=True)
            mock_import.assert_not_called()

    def test_hook_execution_error(self):
        """
        Verify exception is raised when hook execution fails.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_id = "1"
        substeps_cfg = []
        pre_run = "tests.mocks.hooks.pre_run"

        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = Exception("Module not found")

            manager = SubStepManager(
                cfg={},
                logger=mock_logger,
                plugin_manager=mock_plugin_manager,
                step_id=step_id,
                substeps_cfg=substeps_cfg,
                pre_run=pre_run,
            )

            with pytest.raises(AutomaxError) as exc_info:
                manager.run(dry_run=False)

            assert "Failed to execute pre_run hook" in str(exc_info.value)

    def test_no_hooks_when_not_defined(self):
        """
        Verify no errors when hooks are not defined.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_id = "1"
        substeps_cfg = []

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id=step_id,
            substeps_cfg=substeps_cfg,
        )

        result = manager.run(dry_run=False)
        assert result is True
