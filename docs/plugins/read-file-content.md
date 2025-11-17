# Read File Content Plugin

Read content from files.

## Configuration

**Required:**
- `file_path`: Path to the file

**Optional:**
- `encoding`: File encoding (default: utf-8)

## Example

```yaml
plugin: read_file_content
config:
  file_path: "/path/to/config.yaml"
  encoding: "utf-8"
```

## Return Values

The plugin returns a dictionary with:
- `file_path`: The path to the file
- `content`: The content of the file
- `encoding`: The encoding used
- `size`: The size of the content in bytes
- `status`: "success" or "failure"
