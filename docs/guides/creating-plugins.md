# Creating Custom Plugins

This guide explains how to create custom plugins for Automax.

## Plugin Structure

All plugins must inherit from `BasePlugin` and implement the required methods:

```python
from automax.plugins import BasePlugin, PluginMetadata, register_plugin

@register_plugin
class CustomPlugin(BasePlugin):
    METADATA = PluginMetadata(
        name="custom_plugin",
        version="1.0.0",
        description="My custom plugin description",
        author="Your Name",
        category="custom",
        tags=["custom", "example"],
        required_config=["required_param"],
        optional_config=["optional_param"]
    )

    def execute(self) -> Dict[str, Any]:
        # Your plugin logic here
        return {"status": "success", "data": "your result"}
```

## Required Methods

### `execute()`
The main method that performs the plugin's work. Must return a dictionary.

### Metadata
Define plugin metadata including name, version, and configuration requirements.

## Example: Simple File Reader

```python
from pathlib import Path
from typing import Any, Dict

from automax.plugins import BasePlugin, PluginMetadata, register_plugin

@register_plugin
class FileReaderPlugin(BasePlugin):
    METADATA = PluginMetadata(
        name="file_reader",
        version="1.0.0",
        description="Reads content from files",
        author="Marco Fortina",
        category="file_operations",
        tags=["file", "read"],
        required_config=["file_path"],
        optional_config=["encoding"]
    )

    def execute(self) -> Dict[str, Any]:
        file_path = Path(self.config["file_path"])
        encoding = self.config.get("encoding", "utf-8")

        if not file_path.exists():
            raise PluginExecutionError(f"File not found: {file_path}")

        content = file_path.read_text(encoding=encoding)

        return {
            "file_path": str(file_path),
            "content": content,
            "size": len(content)
        }
```

## Best Practices

1. **Error Handling**: Use specific exception types for different error scenarios
2. **Validation**: Validate configuration in `__init__` method
3. **Logging**: Use `self.logger` for consistent logging
4. **Resource Management**: Implement `cleanup()` for resource cleanup
5. **Testing**: Write unit tests for your plugins

## Testing Your Plugin

```python
def test_file_reader():
    config = {"file_path": "test.txt"}
    plugin = FileReaderPlugin(config)
    result = plugin.execute()
    assert "content" in result
```

## Distribution

Place your plugin file in the `src/automax/plugins/` directory or
create a separate package following Python packaging standards.
