# Output Mapping Guide

Automax provides advanced output mapping capabilities to transform and filter data between substeps.

## Overview

Output mapping allows you to:

- Extract specific fields from complex plugin responses
- Filter and transform data before storing in context
- Convert data types and formats
- Create complex data pipelines between substeps

## Basic Usage

### Simple Field Selection

```yaml
substeps:
  - id: "1"
    plugin: "http_request"
    output_mapping:
      source: "data.users.0.name"
      target: "first_user_name"
```

### List Operations

```yaml
substeps:
  - id: "2"
    plugin: "database_operations"
    output_mapping:
      source: "rows"
      transforms:
        - "filter:active==True"
        - "map:item.username"
        - "as:list"
      target: "active_usernames"
```

## Transformation Reference

### Selection Operations

- `select:field.path` - Extract value from nested object
- `select:array.0` - Get array element by index

### Filter Operations

- `filter:field==value` - Filter list by equality
- `filter:field!=value` - Filter list by inequality
- `filter:exists` - Filter non-null values

### Mapping Operations

- `map:item.field` - Extract field from each list item
- `map:expression` - Transform each item using expression

### Type Conversion

- `as:str` - Convert to string
- `as:int` - Convert to integer
- `as:list` - Convert to list
- `as:dict` - Convert to dictionary

### JSON Operations

- `json_parse` - Parse JSON string to object
- `json_stringify` - Convert object to JSON string

## Examples

### Complex Data Pipeline

```yaml
substeps:
  - id: "process_data"
    plugin: "api_call"
    output_mapping:
      source: "response.data.items"
      transforms:
        - "filter:status=='active'"
        - "map:item.id"
        - "as:list"
      target: "active_item_ids"
```

### Multiple Transformations

```yaml
substeps:
  - id: "transform_results"
    plugin: "database_query"
    output_mapping:
      source: "rows"
      transforms:
        - "filter:price>100"
        - "map:item.name"
        - "as:list"
        - "json_stringify"
      target: "expensive_products_json"
```

### Backward Compatibility

The traditional `output_key` approach still works:

```yaml
substeps:
  - id: "legacy"
    plugin: "simple_plugin"
    output_key: "simple_result"
```

## Best Practices

1. **Use descriptive target names** that indicate the transformed data
2. **Chain transformations** from simple to complex
3. **Handle errors** with appropriate fallbacks
4. **Test transformations** with sample data before deployment
5. **Use type conversion** to ensure data consistency

## Error Handling

Output mapping will raise errors for:
- Invalid transformation specifications
- Non-existent source paths
- Type conversion failures
- Malformed JSON data

Always test your output mappings with representative data samples.
