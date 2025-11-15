# Write File Content Plugin

Write content to files.

## Configuration

**Required:**
- `file_path`: Path to the file
- `content`: Content to write

**Optional:**
- `encoding`: File encoding (default: utf-8)
- `mode`: Write mode - w, a, x (default: w)
- `create_dirs`: Create directories if missing (default: false)

## Example

```yaml
plugin: write_file_content
config:
  file_path: "/var/log/app.log"
  content: "Log entry"
  mode: "a"
  create_dirs: true
```
