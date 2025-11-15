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
