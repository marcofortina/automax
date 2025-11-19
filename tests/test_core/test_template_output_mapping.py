"""
Tests for template-based output mapping transformations.
"""

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.managers.template_manager import TemplateManager
from automax.core.utils.data_transformer import DataTransformer


class TestTemplateOutputMapping:
    """
    Test suite for template-based output mapping functionality.
    """

    def test_template_transform_basic(self):
        """
        Verify basic template transformation works.
        """
        config = {}
        context = {}
        template_manager = TemplateManager(config, context)
        transformer = DataTransformer(template_manager)

        data = "hello"
        mapping = {"transforms": ["template:{{ data | upper }}"]}

        result = transformer.transform(data, mapping)

        assert result == "HELLO"

    def test_template_transform_with_complex_data(self):
        """
        Verify template transformation works with complex data structures.
        """
        config = {}
        context = {}
        template_manager = TemplateManager(config, context)
        transformer = DataTransformer(template_manager)

        data = {"name": "Alice", "age": 30}
        mapping = {
            "transforms": ["template:{{ data.name }} is {{ data.age }} years old"]
        }

        result = transformer.transform(data, mapping)

        assert result == "Alice is 30 years old"

    def test_template_transform_with_list_data(self):
        """
        Verify template transformation works with list data.
        """
        config = {}
        context = {}
        template_manager = TemplateManager(config, context)
        transformer = DataTransformer(template_manager)

        data = [1, 2, 3]
        mapping = {"transforms": ["template:{{ data | join(', ') }}"]}

        result = transformer.transform(data, mapping)

        assert result == "1, 2, 3"

    def test_template_transform_with_context_variables(self):
        """
        Verify template transformation can use context variables.
        """
        config = {"environment": "test"}
        context = {"user": "tester"}
        template_manager = TemplateManager(config, context)
        transformer = DataTransformer(template_manager)

        data = "hello"
        mapping = {
            "transforms": [
                "template:{{ data | upper }} in {{ config.environment }} by {{ context.user }}"
            ]
        }

        result = transformer.transform(data, mapping)

        assert result == "HELLO in test by tester"

    def test_template_transform_multiple_transforms(self):
        """
        Verify template transformation works with multiple transforms.
        """
        config = {}
        context = {}
        template_manager = TemplateManager(config, context)
        transformer = DataTransformer(template_manager)

        data = "hello"
        mapping = {
            "transforms": ["template:{{ data | upper }}", "template:{{ data }} world!"]
        }

        result = transformer.transform(data, mapping)

        assert result == "HELLO world!"

    def test_template_transform_without_template_manager(self):
        """
        Verify template transformation fails without TemplateManager.
        """
        transformer = DataTransformer()  # No template manager

        data = "hello"
        mapping = {"transforms": ["template:{{ data | upper }}"]}

        with pytest.raises(AutomaxError) as exc_info:
            transformer.transform(data, mapping)

        assert "Template transforms require a TemplateManager instance" in str(
            exc_info.value
        )

    def test_template_transform_complex_jinja2_logic(self):
        """
        Verify complex Jinja2 logic works in template transformations.
        """
        config = {"threshold": 50}
        context = {}
        template_manager = TemplateManager(config, context)
        transformer = DataTransformer(template_manager)

        data = [{"name": "item1", "value": 30}, {"name": "item2", "value": 60}]
        mapping = {
            "transforms": [
                "template:{{ data | selectattr('value', 'gt', config.threshold) | map(attribute='name') | list }}"
            ]
        }

        result = transformer.transform(data, mapping)

        assert result == "['item2']"

    def test_template_transform_with_filters(self):
        """
        Verify custom filters work in template transformations.
        """
        config = {}
        context = {}
        template_manager = TemplateManager(config, context)

        # Register a custom filter for testing
        def custom_reverse(value):
            return value[::-1]

        template_manager._environment.filters["reverse"] = custom_reverse

        transformer = DataTransformer(template_manager)

        data = "hello"
        mapping = {"transforms": ["template:{{ data | reverse }}"]}

        result = transformer.transform(data, mapping)

        assert result == "olleh"

    def test_template_transform_error_handling(self):
        """
        Verify template transformation properly handles errors.
        """
        config = {}
        context = {}
        template_manager = TemplateManager(config, context)
        transformer = DataTransformer(template_manager)

        data = "hello"
        mapping = {"transforms": ["template:{{ undefined_variable }}"]}

        with pytest.raises(AutomaxError) as exc_info:
            transformer.transform(data, mapping)

        assert "Template transformation failed" in str(exc_info.value)
