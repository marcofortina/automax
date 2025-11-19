"""
Tests for DataTransformer class.
"""

import pytest

from automax.core.exceptions import AutomaxError
from automax.core.utils.data_transformer import DataTransformer


class TestDataTransformer:
    """
    Test suite for DataTransformer functionality.
    """

    def test_transform_no_transforms(self):
        """
        Verify DataTransformer returns data as is when no transforms specified.
        """
        transformer = DataTransformer()
        data = {"key": "value"}
        mapping = {"target": "output_key"}

        result = transformer.transform(data, mapping)

        assert result == data

    def test_transform_builtin_transforms(self):
        """
        Verify DataTransformer applies built-in transforms correctly.
        """
        transformer = DataTransformer()

        # Test string transform
        result = transformer.transform(123, {"transforms": ["string"]})
        assert result == "123"

        # Test int transform
        result = transformer.transform("456", {"transforms": ["int"]})
        assert result == 456

        # Test float transform
        result = transformer.transform("3.14", {"transforms": ["float"]})
        assert result == 3.14

        # Test bool transform
        result = transformer.transform("True", {"transforms": ["bool"]})
        assert result is True

    def test_transform_unknown_transform(self):
        """
        Verify DataTransformer raises error for unknown transforms.
        """
        transformer = DataTransformer()

        with pytest.raises(AutomaxError) as exc_info:
            transformer.transform("data", {"transforms": ["unknown"]})

        assert "Unknown transform" in str(exc_info.value)

    def test_transform_multiple_transforms(self):
        """
        Verify DataTransformer applies multiple transforms in sequence.
        """
        transformer = DataTransformer()

        data = "123"
        mapping = {"transforms": ["int", "string"]}

        result = transformer.transform(data, mapping)

        # First convert to int (123), then to string ("123")
        assert result == "123"

    def test_template_transform_without_template_manager(self):
        """
        Verify DataTransformer raises error for template transforms without
        TemplateManager.
        """
        transformer = DataTransformer()  # No template manager provided

        with pytest.raises(AutomaxError) as exc_info:
            transformer.transform(
                "data", {"transforms": ["template:{{ data | upper }}"]}
            )

        assert "Template transforms require a TemplateManager instance" in str(
            exc_info.value
        )
