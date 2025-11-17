"""
Tests for DataTransformer utility class.
"""

import pytest

from automax.core.utils.data_transformer import DataTransformer


class TestDataTransformer:
    """
    Test suite for DataTransformer functionality.
    """

    def test_select_path_simple_dict(self):
        """
        Test selecting values from simple dictionary.
        """
        data = {"name": "John", "age": 30}
        result = DataTransformer.transform(data, "select:name")
        assert result == "John"

    def test_select_path_nested_dict(self):
        """
        Test selecting values from nested dictionary.
        """
        data = {"user": {"profile": {"name": "Alice"}}}
        result = DataTransformer.transform(data, "select:user.profile.name")
        assert result == "Alice"

    def test_select_path_list_index(self):
        """
        Test selecting values from list by index.
        """
        data = {"items": ["first", "second", "third"]}
        result = DataTransformer.transform(data, "select:items.1")
        assert result == "second"

    def test_filter_list_simple(self):
        """
        Test filtering list with simple condition.
        """
        data = [
            {"name": "Alice", "active": True},
            {"name": "Bob", "active": False},
            {"name": "Charlie", "active": True},
        ]
        result = DataTransformer.transform(data, "filter:active==True")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Charlie"

    def test_map_list_field_extraction(self):
        """
        Test mapping list to extract specific fields.
        """
        data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
        result = DataTransformer.transform(data, "map:item.name")
        assert result == ["Alice", "Bob"]

    def test_type_conversion_string(self):
        """
        Test type conversion to string.
        """
        result = DataTransformer.transform(123, "as:str")
        assert result == "123"

    def test_type_conversion_list(self):
        """
        Test type conversion to list.
        """
        result = DataTransformer.transform("single", "as:list")
        assert result == ["single"]

    def test_json_parsing(self):
        """
        Test JSON string parsing.
        """
        json_str = '{"name": "John", "age": 30}'
        result = DataTransformer.transform(json_str, "json_parse")
        assert result == {"name": "John", "age": 30}

    def test_json_stringify(self):
        """
        Test JSON stringification.
        """
        data = {"name": "John", "age": 30}
        result = DataTransformer.transform(data, "json_stringify")
        assert '"name": "John"' in result
        assert '"age": 30' in result

    def test_transform_pipeline(self):
        """
        Test complex transformation pipeline.
        """
        data = {
            "response": {
                "users": [
                    {"name": "alice", "active": True, "age": 25},
                    {"name": "bob", "active": False, "age": 30},
                    {"name": "charlie", "active": True, "age": 35},
                ]
            }
        }

        pipeline = {
            "source": "response.users",
            "transforms": ["filter:active==True", "map:item.name", "as:list"],
        }

        result = DataTransformer.transform(data, pipeline)
        assert result == ["alice", "charlie"]

    def test_invalid_transform(self):
        """
        Test handling of invalid transformation.
        """
        with pytest.raises(ValueError, match="Unknown transformation"):
            DataTransformer.transform({}, "invalid:transform")

    def test_none_handling(self):
        """
        Test transformation with None values.
        """
        result = DataTransformer.transform(None, "as:str")
        assert result == ""

    def test_empty_string_handling(self):
        """
        Test transformation with empty strings.
        """
        result = DataTransformer.transform("", "as:int")
        assert result == 0

    def test_invalid_string_to_int(self):
        """
        Test conversion of invalid string to integer.
        """
        result = DataTransformer.transform("invalid", "as:int")
        assert result == 0

    def test_empty_string_to_bool(self):
        """
        Test conversion of empty string to boolean.
        """
        result = DataTransformer.transform("", "as:bool")
        assert result is False
