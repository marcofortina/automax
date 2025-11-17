# Write File Content Plugin

Write content to files.

## Configuration

**Required:**
- `file_path`: Path to the file
- `content`: Content to write

**Optional:**
- `encoding`: File encoding (default: utf-8)
- `mode`: Write mode - "w", "a", "x" (default: w)
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

## Return Values

The plugin returns a dictionary with:
- `file_path`: The path to the file
- `content_length`: The length of the written content
- `file_size`: The size of the file after writing
- `encoding`: The encoding used
- `mode`: The write mode used
- `create_dirs`: Whether directories were created
- `status`: "success" or "failure"
