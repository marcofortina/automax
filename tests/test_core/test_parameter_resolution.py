"""
Tests for parameter resolution functionality.
"""

from unittest.mock import MagicMock

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.substep_manager import SubStepManager


class TestParameterResolution:
    """
    Test parameter resolution with context and environment variables.
    """

    def test_resolve_config_placeholders(self):
        """
        Verify config placeholders are resolved correctly.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg={"temp_dir": "/tmp", "user": "testuser"},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        params = {"path": "{temp_dir}/files", "user": "{user}"}
        resolved = manager._resolve_params(params)

        assert resolved["path"] == "/tmp/files"
        assert resolved["user"] == "testuser"

    def test_resolve_context_placeholders(self):
        """
        Verify context placeholders are resolved correctly.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        # Set up context
        manager.context = {"output_file": "result.txt", "count": 5}

        params = {"file": "{output_file}", "total": "count: {count}"}
        resolved = manager._resolve_params(params)

        assert resolved["file"] == "result.txt"
        assert resolved["total"] == "count: 5"

    def test_resolve_environment_variables(self):
        """
        Verify environment variables are resolved correctly.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        params = {"home": "$HOME", "path": "/tmp/$USER"}
        resolved = manager._resolve_params(params)

        # These will be expanded by os.path.expandvars
        assert "$" not in resolved["home"] or resolved["home"] != "$HOME"
        assert "$" not in resolved["path"] or resolved["path"] != "/tmp/$USER"

    def test_missing_placeholder_key(self):
        """
        Verify error is raised for missing placeholder keys.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        params = {"path": "{missing_key}/files"}

        with pytest.raises(AutomaxError) as exc_info:
            manager._resolve_params(params)

        assert "Missing placeholder key" in str(exc_info.value)

    def test_context_sharing_between_substeps(self):
        """
        Verify context is shared between subsequent sub-steps.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        # Mock plugin execution
        def mock_execute():
            return "mock_output_data"

        mock_plugin_class = MagicMock()
        mock_plugin_instance = MagicMock()
        mock_plugin_instance.execute = MagicMock(return_value="mock_output_data")
        mock_plugin_class.return_value = mock_plugin_instance
        mock_plugin_manager.get_plugin.return_value = mock_plugin_class

        substeps_cfg = [
            {
                "id": "1",
                "description": "First step with output",
                "plugin": "test_plugin",
                "params": {},
                "output_key": "first_output",
            },
            {
                "id": "2",
                "description": "Second step using output",
                "plugin": "test_plugin",
                "params": {"input": "{first_output}"},
            },
        ]

        manager = SubStepManager(
            cfg={},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=substeps_cfg,
        )

        manager.run()

        # Verify context was populated and used
        assert "first_output" in manager.context
        assert manager.context["first_output"] == "mock_output_data"
