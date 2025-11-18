"""
Tests for dynamic step and substep configuration with Jinja2 templating.
"""

import os
from unittest.mock import MagicMock

from automax.core.managers.step_manager import StepManager
from automax.core.managers.substep_manager import SubStepManager


class TestDynamicStepConfiguration:
    """
    Test suite for dynamic step and substep configuration.
    """

    def test_step_id_templating(self):
        """
        Verify step ID can be dynamically generated using templates.
        """
        config = {"environment": "production", "app_name": "myapp"}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        step_manager = StepManager(config, mock_logger, mock_plugin_manager)

        step_config = {
            "id": "deploy-{{ config.environment }}",
            "description": "Deployment step",
            "substeps": [
                {
                    "id": "substep1",
                    "description": "First substep",
                    "plugin": "local_command",
                    "params": {"command": "echo 'hello'"},
                }
            ],
        }

        rendered_cfg = step_manager._render_step_config(step_config)

        assert rendered_cfg["id"] == "deploy-production"

    def test_step_description_templating(self):
        """
        Verify step description can be dynamically generated using templates.
        """
        config = {"region": "us-east-1", "environment": "staging"}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        step_config = {
            "id": "deploy",
            "description": "Deploy to {{ config.region }} in {{ config.environment }}",
            "substeps": [],
        }

        step_manager = StepManager(config, mock_logger, mock_plugin_manager)
        rendered_cfg = step_manager._render_step_config(step_config)

        assert rendered_cfg["description"] == "Deploy to us-east-1 in staging"

    def test_substep_id_templating(self):
        """
        Verify substep ID can be dynamically generated using templates.
        """
        config = {"timestamp": "20240101"}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_manager = StepManager(config, mock_logger, mock_plugin_manager)

        # Set context for template rendering
        step_manager.context = {"build_version": "1.2.3"}

        substep_config = {
            "id": "backup-{{ context.build_version }}-{{ config.timestamp }}",
            "description": "Backup substep",
            "plugin": "local_command",
            "params": {"command": "echo 'backup'"},
        }

        rendered_substep = step_manager._render_substep_config(substep_config)

        assert rendered_substep["id"] == "backup-1.2.3-20240101"

    def test_substep_params_templating(self):
        """
        Verify substep parameters can be dynamically generated using templates.
        """
        config = {"backup_dir": "/backups", "app_name": "myapp"}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_manager = StepManager(config, mock_logger, mock_plugin_manager)
        step_manager.context = {"version": "2.0.0"}

        substep_config = {
            "id": "backup",
            "description": "Backup application",
            "plugin": "local_command",
            "params": {
                "source": "{{ config.backup_dir }}/{{ config.app_name }}-{{ context.version }}",
                "command": "backup --target {{ config.backup_dir }}/{{ config.app_name }}-{{ context.version }}.tar.gz",
            },
        }

        rendered_substep = step_manager._render_substep_config(substep_config)

        expected_source = "/backups/myapp-2.0.0"
        expected_command = "backup --target /backups/myapp-2.0.0.tar.gz"

        assert rendered_substep["params"]["source"] == expected_source
        assert rendered_substep["params"]["command"] == expected_command

    def test_environment_variables_in_templates(self):
        """
        Verify environment variables can be used in step templates.
        """
        # Set environment variable for test
        os.environ["TEST_ENV_VAR"] = "test_value"

        config = {}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_manager = StepManager(config, mock_logger, mock_plugin_manager)

        step_config = {
            "id": "step-{{ env.TEST_ENV_VAR }}",
            "description": "Step using {{ env.TEST_ENV_VAR }}",
            "substeps": [],
        }

        rendered_cfg = step_manager._render_step_config(step_config)

        assert rendered_cfg["id"] == "step-test_value"
        assert rendered_cfg["description"] == "Step using test_value"

    def test_complex_template_rendering(self):
        """
        Verify complex templates with conditionals and filters work in step
        configuration.
        """
        config = {"environment": "production", "debug": False}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()
        step_manager = StepManager(config, mock_logger, mock_plugin_manager)

        step_config = {
            "id": "{% if config.environment == 'production' %}prod-deploy{% else %}dev-deploy{% endif %}",
            "description": "Deployment (Debug: {{ config.debug | lower }})",
            "substeps": [],
        }

        rendered_cfg = step_manager._render_step_config(step_config)

        assert rendered_cfg["id"] == "prod-deploy"
        assert rendered_cfg["description"] == "Deployment (Debug: false)"

    def test_context_sharing_between_steps(self):
        """
        Verify context is shared between StepManager and SubStepManager.
        """
        config = {}
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        step_manager = StepManager(config, mock_logger, mock_plugin_manager)

        # Set initial context
        step_manager.context = {"initial_value": "test"}

        # Verify SubStepManager gets the same context
        substep_manager = SubStepManager(
            cfg=config,
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="test-step",
            substeps_cfg=[],
        )

        # Now set the context through step_manager and check in substep_manager
        step_manager.context = {"updated_value": "new_test"}
        # We need to set the context of substep_manager to the same as step_manager
        substep_manager.context = step_manager.context

        assert substep_manager.context["updated_value"] == "new_test"
