"""
Data transformation utilities for output mapping.

Supports various transformation types including template-based transformations.

"""

from automax.core.exceptions import AutomaxError
from automax.core.managers.template_manager import TemplateManager


class DataTransformer:
    """
    Transforms data based on mapping configurations.
    """

    def __init__(self, template_manager: TemplateManager = None):
        """
        Initialize DataTransformer.

        Args:
            template_manager: TemplateManager instance for template transforms.

        """
        self.template_manager = template_manager

    def transform(self, data: any, mapping: dict) -> any:
        """
        Transform data based on mapping configuration.

        Args:
            data: Input data to transform.
            mapping: Transformation mapping configuration.

        Returns:
            Transformed data.

        Raises:
            AutomaxError: If transformation fails.

        """
        try:
            # Extract source if specified
            if "source" in mapping:
                data = self._extract_field(data, mapping["source"])

            # If no transforms specified, return data as is
            transforms = mapping.get("transforms", [])
            if not transforms:
                return data

            # Apply transforms sequentially
            transformed_data = data
            for transform in transforms:
                transformed_data = self._apply_transform(
                    transformed_data, transform, mapping
                )

            return transformed_data

        except Exception as e:
            raise AutomaxError(f"Data transformation failed: {e}")

    def _extract_field(self, data: any, field_path: str) -> any:
        """
        Extract a nested field from data using dot notation.

        Args:
            data: Input data.
            field_path: Dot-separated path to the field.

        Returns:
            Extracted field value.

        Raises:
            AutomaxError: If field is not found.

        """
        current = data
        for part in field_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise AutomaxError(f"Field '{part}' not found at path '{field_path}'")
        return current

    def _apply_transform(self, data: any, transform: str, mapping: dict) -> any:
        """
        Apply a single transformation to data.

        Args:
            data: Input data.
            transform: Transformation string (e.g., "template:{{ data | upper }}").
            mapping: Full mapping configuration for context.

        Returns:
            Transformed data.

        Raises:
            AutomaxError: If transform type is unknown.

        """
        # Check if it's a template transform
        if transform.startswith("template:"):
            template_string = transform[len("template:") :]
            return self._apply_template_transform(data, template_string, mapping)

        # Check if it's a filter transform
        if transform.startswith("filter:"):
            condition = transform[len("filter:") :]
            return self._apply_filter_transform(data, condition)

        # Check if it's a map transform
        if transform.startswith("map:"):
            expression = transform[len("map:") :]
            return self._apply_map_transform(data, expression)

        # Check if it's an "as" transform (e.g., "as:list")
        if transform.startswith("as:"):
            type_name = transform[len("as:") :]
            return self._apply_as_transform(data, type_name)

        # Check if it's a built-in transform
        if transform in DataTransformer._BUILTIN_TRANSFORMS:
            return DataTransformer._BUILTIN_TRANSFORMS[transform](data)

        raise AutomaxError(f"Unknown transform: {transform}")

    def _apply_template_transform(
        self, data: any, template_string: str, mapping: dict
    ) -> any:
        """
        Apply a template transformation to data.

        Args:
            data: Input data.
            template_string: Jinja2 template string.
            mapping: Full mapping configuration for context.

        Returns:
            Transformed data.

        Raises:
            AutomaxError: If template rendering fails.

        """
        if not self.template_manager:
            raise AutomaxError(
                "Template transforms require a TemplateManager instance."
            )

        # Prepare the context for the template
        extra_context = {"data": data}

        try:
            rendered = self.template_manager.render(template_string, extra_context)
            return rendered
        except Exception as e:
            raise AutomaxError(f"Template transformation failed: {e}")

    def _apply_filter_transform(self, data: any, condition: str) -> any:
        """
        Apply a filter transformation to data.

        Args:
            data: Input data (should be a list).
            condition: Filter condition (e.g., "active==True").

        Returns:
            Filtered data.

        Raises:
            AutomaxError: If data is not a list or condition is invalid.

        """
        if not isinstance(data, list):
            raise AutomaxError("Filter transform can only be applied to lists")

        # Parse condition (simple equality for now)
        if "==" not in condition:
            raise AutomaxError("Filter condition must use '==' operator")

        field, value = condition.split("==", 1)
        field = field.strip()
        value = value.strip()

        # Convert value to appropriate type
        if value == "True":
            value = True
        elif value == "False":
            value = False
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

        # Apply filter
        filtered_data = []
        for item in data:
            if isinstance(item, dict) and item.get(field) == value:
                filtered_data.append(item)
            elif hasattr(item, field) and getattr(item, field) == value:
                filtered_data.append(item)

        return filtered_data

    def _apply_map_transform(self, data: any, expression: str) -> any:
        """
        Apply a map transformation to data.

        Args:
            data: Input data (should be a list).
            expression: Mapping expression (e.g., "item.name").

        Returns:
            Mapped data.

        Raises:
            AutomaxError: If data is not a list or expression is invalid.

        """
        if not isinstance(data, list):
            raise AutomaxError("Map transform can only be applied to lists")

        # Parse expression (simple field access for now)
        if not expression.startswith("item."):
            raise AutomaxError("Map expression must start with 'item.'")

        field = expression[5:]  # Remove "item."

        # Apply map
        mapped_data = []
        for item in data:
            if isinstance(item, dict) and field in item:
                mapped_data.append(item[field])
            elif hasattr(item, field):
                mapped_data.append(getattr(item, field))
            else:
                # Skip items that don't have the field
                continue

        return mapped_data

    def _apply_as_transform(self, data: any, type_name: str) -> any:
        """
        Apply an "as" transformation to convert data to a specific type.

        Args:
            data: Input data.
            type_name: Target type name.

        Returns:
            Converted data.

        Raises:
            AutomaxError: If conversion fails.

        """
        if type_name == "list":
            if not isinstance(data, list):
                return [data]
            return data
        elif type_name == "dict":
            if not isinstance(data, dict):
                # Try to convert to dict if possible
                if hasattr(data, "__dict__"):
                    return data.__dict__
                else:
                    raise AutomaxError("Cannot convert data to dict")
            return data
        else:
            raise AutomaxError(f"Unknown type for 'as' transform: {type_name}")

    # Built-in transforms
    _BUILTIN_TRANSFORMS = {
        "string": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
    }
