"""
Tests for Jinja2 templating integration in parameter resolution.
"""

import os
from unittest.mock import MagicMock

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.substep_manager import SubStepManager


class TestJinja2Templating:
    """
    Test suite for Jinja2 templating functionality.
    """

    def test_jinja2_config_placeholder(self):
        """
        Verify Jinja2 template resolution with config values.
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

        params = {"path": "{{ config.temp_dir }}/files", "user": "{{ config.user }}"}
        resolved = manager._resolve_params(params)

        assert resolved["path"] == "/tmp/files"
        assert resolved["user"] == "testuser"

    def test_jinja2_context_placeholder(self):
        """
        Verify Jinja2 template resolution with context values.
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

        params = {
            "file": "{{ context.output_file }}",
            "total": "count: {{ context.count }}",
        }
        resolved = manager._resolve_params(params)

        assert resolved["file"] == "result.txt"
        assert resolved["total"] == "count: 5"

    def test_jinja2_environment_variables(self):
        """
        Verify Jinja2 template resolution with environment variables.
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

        # Set environment variable for test
        os.environ["TEST_JINJA2_VAR"] = "test_value"

        params = {"test_var": "{{ env.TEST_JINJA2_VAR }}"}
        resolved = manager._resolve_params(params)

        assert resolved["test_var"] == "test_value"

    def test_jinja2_complex_template(self):
        """
        Verify Jinja2 template resolution with complex expressions.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg={"base_path": "/app", "environment": "production"},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        manager.context = {"version": "2.1.0"}

        params = {
            "path": "{{ config.base_path }}/releases/{{ context.version }}",
            "env": "Environment: {{ config.environment | upper }}",
            "combined": "{{ config.base_path }}_{{ config.environment }}_{{ context.version }}",
        }
        resolved = manager._resolve_params(params)

        assert resolved["path"] == "/app/releases/2.1.0"
        assert resolved["env"] == "Environment: PRODUCTION"
        assert resolved["combined"] == "/app_production_2.1.0"

    def test_jinja2_template_error(self):
        """
        Verify error handling for invalid Jinja2 templates.
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

        params = {"invalid": "{{ undefined_variable }}"}

        with pytest.raises(AutomaxError) as exc_info:
            manager._resolve_params(params)

        assert "Template rendering failed" in str(exc_info.value)

    def test_backward_compatibility_legacy_placeholders(self):
        """
        Verify backward compatibility with legacy placeholder syntax.
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

        manager.context = {"output_file": "result.txt"}

        # Set environment variable for test
        os.environ["TEST_LEGACY_VAR"] = "legacy_value"

        params = {
            "path": "{temp_dir}/files",
            "file": "{output_file}",
            "env_var": "$TEST_LEGACY_VAR",
        }
        resolved = manager._resolve_params(params)

        assert resolved["path"] == "/tmp/files"
        assert resolved["file"] == "result.txt"
        assert resolved["env_var"] == "legacy_value"

    def test_mixed_jinja2_and_legacy_syntax(self):
        """
        Verify that strings without Jinja2 syntax use legacy resolution.
        """
        mock_logger = MagicMock()
        mock_plugin_manager = MagicMock()

        manager = SubStepManager(
            cfg={"temp_dir": "/tmp"},
            logger=mock_logger,
            plugin_manager=mock_plugin_manager,
            step_id="1",
            substeps_cfg=[],
        )

        # String without Jinja2 syntax should use legacy resolution
        params = {"path": "{temp_dir}/files"}
        resolved = manager._resolve_params(params)

        assert resolved["path"] == "/tmp/files"

    def test_non_string_parameters_unchanged(self):
        """
        Verify that non-string parameters are passed through unchanged.
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

        params = {
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "none": None,
        }
        resolved = manager._resolve_params(params)

        assert resolved["number"] == 42
        assert resolved["boolean"] is True
        assert resolved["list"] == [1, 2, 3]
        assert resolved["dict"] == {"key": "value"}
        assert resolved["none"] is None
