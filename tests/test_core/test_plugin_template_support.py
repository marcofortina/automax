"""
Tests for plugin template support in parameter resolution.
"""

from unittest.mock import MagicMock

from automax.core.managers.substep_manager import SubStepManager


class TestPluginTemplateSupport:
    """
    Test suite for plugin template support in SubStepManager.
    """

    def test_plugin_parameters_with_explicit_template_flag(self):
        """
        Verify plugin parameters with is_template flag are properly resolved.
        """
        config = {"environment": "production", "app_name": "myapp"}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg=config,
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        # Simulate parameters for write_file_content plugin with explicit template flag
        params = {
            "file_path": "/opt/{{ config.app_name }}/config.yaml",
            "content": "Hello {{ config.environment }}",
            "content_is_template": True,
        }

        resolved = manager._resolve_params(params)

        assert resolved["file_path"] == "/opt/myapp/config.yaml"
        assert resolved["content"] == "Hello production"
        assert "content_is_template" not in resolved  # Flag should be removed

    def test_plugin_parameters_auto_template_detection(self):
        """
        Verify plugin parameters with template patterns are auto-detected.
        """
        config = {"region": "us-east-1"}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg=config,
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        params = {
            "path": "/deploy/{{ config.region }}/app",  # Auto-detected template
            "command": "echo 'static command'",  # No template
        }

        resolved = manager._resolve_params(params)

        assert resolved["path"] == "/deploy/us-east-1/app"
        assert resolved["command"] == "echo 'static command'"

    def test_plugin_parameters_mixed_approaches(self):
        """
        Verify mixed template approaches work correctly.
        """
        config = {"env": "staging", "debug": True}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg=config,
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        params = {
            "auto_template": "Auto: {{ config.env }}",  # Auto-detected
            "explicit_template": "Explicit: {{ config.debug }}",
            "explicit_template_is_template": True,
            "legacy_placeholder": "Legacy: {env}",  # Legacy style
            "static_value": "plain text",
        }

        resolved = manager._resolve_params(params)

        assert resolved["auto_template"] == "Auto: staging"
        assert resolved["explicit_template"] == "Explicit: True"
        assert resolved["legacy_placeholder"] == "Legacy: staging"
        assert resolved["static_value"] == "plain text"
        assert "explicit_template_is_template" not in resolved  # Flag removed
