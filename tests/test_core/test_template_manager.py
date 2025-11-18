"""
Tests for TemplateManager class.
"""

import os

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.template_manager import TemplateManager


class TestTemplateManager:
    """
    Test suite for TemplateManager functionality.
    """

    def test_template_manager_initialization(self):
        """
        Verify TemplateManager can be initialized with config and context.
        """
        config = {"temp_dir": "/tmp", "user": "testuser"}
        context = {"output_file": "result.txt"}

        manager = TemplateManager(config, context)
        assert manager.config == config
        assert manager.context == context

    def test_template_manager_render_basic(self):
        """
        Verify TemplateManager can render basic templates.
        """
        config = {"temp_dir": "/tmp", "user": "testuser"}
        context = {"output_file": "result.txt"}

        manager = TemplateManager(config, context)
        result = manager.render(
            "Path: {{ config.temp_dir }}, File: {{ context.output_file }}"
        )

        assert result == "Path: /tmp, File: result.txt"

    def test_template_manager_render_with_filters(self):
        """
        Verify TemplateManager can render templates with filters.
        """
        config = {"environment": "production"}
        manager = TemplateManager(config)

        result = manager.render("Environment: {{ config.environment | upper }}")
        assert result == "Environment: PRODUCTION"

    def test_template_manager_render_with_environment_variables(self):
        """
        Verify TemplateManager can render templates with environment variables.
        """
        manager = TemplateManager({})

        # Set environment variable for test
        os.environ["TEST_TEMPLATE_VAR"] = "test_value"

        result = manager.render("Value: {{ env.TEST_TEMPLATE_VAR }}")
        assert result == "Value: test_value"

    def test_template_manager_render_dict(self):
        """
        Verify TemplateManager can render templates in a dictionary.
        """
        config = {"base_path": "/app"}
        context = {"version": "1.0.0"}
        manager = TemplateManager(config, context)

        data = {
            "path": "{{ config.base_path }}/v{{ context.version }}",
            "name": "app-{{ context.version }}",
            "static_value": "fixed",
        }

        rendered = manager.render_dict(data)

        assert rendered["path"] == "/app/v1.0.0"
        assert rendered["name"] == "app-1.0.0"
        assert rendered["static_value"] == "fixed"

    def test_template_manager_render_dict_nested(self):
        """
        Verify TemplateManager can render templates in nested dictionaries.
        """
        config = {"app_name": "myapp"}
        manager = TemplateManager(config)

        data = {
            "service": {
                "name": "{{ config.app_name }}-service",
                "config": {"path": "/opt/{{ config.app_name }}"},
            },
            "list": ["item-{{ config.app_name }}", "static"],
        }

        rendered = manager.render_dict(data)

        assert rendered["service"]["name"] == "myapp-service"
        assert rendered["service"]["config"]["path"] == "/opt/myapp"
        assert rendered["list"][0] == "item-myapp"
        assert rendered["list"][1] == "static"

    def test_template_manager_error_handling(self):
        """
        Verify TemplateManager properly handles template errors.
        """
        manager = TemplateManager({})

        with pytest.raises(AutomaxError) as exc_info:
            manager.render("{{ undefined_variable }}")

        assert "Template rendering failed" in str(exc_info.value)

    def test_template_manager_extra_context(self):
        """
        Verify TemplateManager can use extra context in rendering.
        """
        manager = TemplateManager({"base": "value"})

        result = manager.render(
            "Base: {{ config.base }}, Extra: {{ extra.value }}",
            extra_context={"extra": {"value": "extra_value"}},
        )

        assert result == "Base: value, Extra: extra_value"

    def test_template_manager_complex_template(self):
        """
        Verify TemplateManager can handle complex templates with conditionals.
        """
        config = {"environment": "production", "debug": False}
        context = {"user_count": 150}
        manager = TemplateManager(config, context)

        template = """{% if config.environment == 'production' %}
Production Environment
Users: {{ context.user_count }}
Debug: {{ config.debug | lower }}
{% else %}
Development Environment
{% endif %}"""

        result = manager.render(template)
        # Remove trailing whitespace for consistent comparison
        result = result.strip()
        expected = "Production Environment\nUsers: 150\nDebug: false"

        assert result == expected

    def test_template_manager_missing_attributes(self):
        """
        Verify TemplateManager handles missing attributes gracefully.
        """
        config = {"existing_key": "value"}
        context = {}
        manager = TemplateManager(config, context)

        # Should not raise an error for missing attributes
        result = manager.render(
            "Existing: {{ config.existing_key }}, Missing: {{ config.missing_key }}"
        )
        assert "Existing: value, Missing: " in result
