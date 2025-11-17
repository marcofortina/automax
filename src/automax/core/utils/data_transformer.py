"""
Data transformation utilities for output mapping between substeps.

Provides advanced data transformation capabilities including filtering, mapping,
selection, and type conversion for complex output mapping scenarios.

"""

import json
from typing import Any, Dict, List, Union


class DataTransformer:
    """
    Transforms data using various operations for output mapping between substeps.
    """

    @staticmethod
    def transform(data: Any, transform_spec: Union[str, Dict]) -> Any:
        """
        Transform data according to transformation specification.

        Args:
            data: Input data to transform
            transform_spec: Transformation specification (string or dict)

        Returns:
            Transformed data

        Raises:
            ValueError: If transformation specification is invalid

        """
        if isinstance(transform_spec, str):
            return DataTransformer._apply_single_transform(data, transform_spec)
        elif isinstance(transform_spec, dict):
            return DataTransformer._apply_transform_pipeline(data, transform_spec)
        else:
            raise ValueError(f"Invalid transform specification: {transform_spec}")

    @staticmethod
    def _apply_single_transform(data: Any, transform: str) -> Any:
        """
        Apply a single transformation to data.

        Args:
            data: Input data
            transform: Transformation string (e.g., "filter:status==active")

        Returns:
            Transformed data

        """
        # Handle simple field selection
        if transform.startswith("select:"):
            path = transform[7:].strip()
            return DataTransformer._select_path(data, path)

        # Handle filtering
        elif transform.startswith("filter:"):
            condition = transform[7:].strip()
            return DataTransformer._filter_list(data, condition)

        # Handle mapping
        elif transform.startswith("map:"):
            expression = transform[4:].strip()
            return DataTransformer._map_list(data, expression)

        # Handle type conversion
        elif transform.startswith("as:"):
            type_name = transform[3:].strip()
            return DataTransformer._convert_type(data, type_name)

        # Handle JSON parsing
        elif transform == "json_parse":
            return DataTransformer._parse_json(data)

        # Handle JSON stringification
        elif transform == "json_stringify":
            return DataTransformer._stringify_json(data)

        else:
            raise ValueError(f"Unknown transformation: {transform}")

    @staticmethod
    def _apply_transform_pipeline(data: Any, pipeline: Dict) -> Any:
        """
        Apply a pipeline of transformations to data.

        Args:
            data: Input data
            pipeline: Pipeline configuration with source and transforms

        Returns:
            Transformed data after applying entire pipeline

        """
        # Extract data from source path if specified
        current_data = data
        if "source" in pipeline:
            current_data = DataTransformer._select_path(data, pipeline["source"])

        # Apply transformations in sequence
        if "transforms" in pipeline:
            for transform in pipeline["transforms"]:
                current_data = DataTransformer.transform(current_data, transform)

        return current_data

    @staticmethod
    def _select_path(data: Any, path: str) -> Any:
        """
        Select data using dot notation path.

        Args:
            data: Input data (dict, list, or scalar)
            path: Dot-separated path (e.g., "data.items.0.name")

        Returns:
            Selected data at specified path

        """
        if not path or path == ".":
            return data

        current = data
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                # Try to access as attribute for objects
                try:
                    current = getattr(current, part)
                except (AttributeError, TypeError):
                    return None

        return current

    @staticmethod
    def _filter_list(data: List, condition: str) -> List:
        """
        Filter list based on condition.

        Args:
            data: List to filter
            condition: Filter condition (e.g., "status=='active'")

        Returns:
            Filtered list

        """
        if not isinstance(data, list):
            return data

        try:
            # Simple condition evaluation for common patterns
            filtered = []
            for item in data:
                if DataTransformer._evaluate_condition(item, condition):
                    filtered.append(item)
            return filtered
        except Exception as e:
            raise ValueError(f"Failed to evaluate filter condition '{condition}': {e}")

    @staticmethod
    def _map_list(data: List, expression: str) -> List:
        """
        Map list using transformation expression.

        Args:
            data: List to transform
            expression: Mapping expression (e.g., "item.name")

        Returns:
            Transformed list

        """
        if not isinstance(data, list):
            return data

        try:
            mapped = []
            for item in data:
                # Simple field extraction
                if expression.startswith("item."):
                    field = expression[5:]
                    value = DataTransformer._select_path(item, field)
                    mapped.append(value)
                else:
                    # For more complex expressions, use the expression as a template
                    result = expression.replace("item", str(item))
                    mapped.append(result)
            return mapped
        except Exception as e:
            raise ValueError(f"Failed to apply map expression '{expression}': {e}")

    @staticmethod
    def _convert_type(data: Any, type_name: str) -> Any:
        """
        Convert data to specified type.

        Args:
            data: Data to convert
            type_name: Target type (str, int, float, bool, list, dict)

        Returns:
            Converted data

        """
        type_name = type_name.lower()

        if type_name == "str":
            return str(data) if data is not None else ""
        elif type_name == "int":
            if data is None or data == "":
                return 0
            try:
                return int(data)
            except (ValueError, TypeError):
                return 0
        elif type_name == "float":
            if data is None or data == "":
                return 0.0
            try:
                return float(data)
            except (ValueError, TypeError):
                return 0.0
        elif type_name == "bool":
            if isinstance(data, str):
                if data.lower() in ("true", "yes", "1", "on"):
                    return True
                elif data.lower() in ("false", "no", "0", "off", ""):
                    return False
            return bool(data)
        elif type_name == "list":
            if isinstance(data, list):
                return data
            elif data is None:
                return []
            else:
                return [data]
        elif type_name == "dict":
            if isinstance(data, dict):
                return data
            elif data is None:
                return {}
            else:
                return {"value": data}
        else:
            raise ValueError(f"Unsupported type conversion: {type_name}")

    @staticmethod
    def _parse_json(data: Any) -> Any:
        """
        Parse JSON string into Python object.

        Args:
            data: JSON string to parse

        Returns:
            Parsed Python object

        """
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return data

    @staticmethod
    def _stringify_json(data: Any) -> str:
        """
        Convert Python object to JSON string.

        Args:
            data: Python object to serialize

        Returns:
            JSON string representation

        """
        try:
            return json.dumps(data, default=str)
        except (TypeError, ValueError):
            return str(data)

    @staticmethod
    def _evaluate_condition(item: Any, condition: str) -> bool:
        """
        Evaluate simple condition against item.

        Args:
            item: Item to evaluate condition against
            condition: Condition expression

        Returns:
            Boolean result of condition evaluation

        """
        # Handle common equality patterns
        if "==" in condition:
            field, value = condition.split("==", 1)
            field = field.strip()
            value = value.strip().strip("'\"")
            field_value = DataTransformer._select_path(item, field)
            return str(field_value) == value

        # Handle inequality patterns
        elif "!=" in condition:
            field, value = condition.split("!=", 1)
            field = field.strip()
            value = value.strip().strip("'\"")
            field_value = DataTransformer._select_path(item, field)
            return str(field_value) != value

        # Handle existence check
        elif condition == "exists":
            return item is not None

        # Default: treat as boolean expression
        else:
            return bool(DataTransformer._select_path(item, condition))
