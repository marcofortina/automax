# Write File Content Plugin

Write content to files on the local filesystem.

## Description

This plugin enables writing content to files with support for different encoding formats, file modes, and automatic directory creation. It can handle both text and binary content.

## Configuration

### Required Parameters

- `file_path` (string): Path to the file to write
- `content` (string): Content to write to the file

### Optional Parameters

- `encoding` (string): File encoding (default: utf-8)
- `mode` (string): File write mode - `overwrite`, `append`, or `create_new` (default: overwrite)
- `create_dirs` (boolean): Create parent directories if they don't exist (default: true)

## Examples

### Write Text File (Overwrite)

```yaml
- name: write_config_file
  plugin: write_file_content
  parameters:
    file_path: "/etc/automax/config.yaml"
    content: |
      database:
        host: localhost
        port: 5432
        name: automax
      logging:
        level: INFO
    encoding: "utf-8"
    mode: "overwrite"
```

### Append to Existing File

```yaml
- name: append_log_entry
  plugin: write_file_content
  parameters:
    file_path: "/var/log/automax.log"
    content: "2024-01-01 12:00:00 - Task completed successfully\n"
    mode: "append"
    create_dirs: true
```

### Write JSON Content

```yaml
- name: write_json_config
  plugin: write_file_content
  parameters:
    file_path: "/app/config.json"
    content: '{"database": {"host": "localhost", "port": 5432}, "features": {"enabled": true}}'
    encoding: "utf-8"
```

### Create New File Only (Fail if Exists)

```yaml
- name: create_new_lockfile
  plugin: write_file_content
  parameters:
    file_path: "/tmp/automax.lock"
    content: "process_12345"
    mode: "create_new"
```

### Write with Different Encoding

```yaml
- name: write_encoded_file
  plugin: write_file_content
  parameters:
    file_path: "/data/output.txt"
    content: "Special characters: ñáéíóú"
    encoding: "utf-16"
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "file_path": "/etc/automax/config.yaml",
  "content_length": 125,
  "mode": "overwrite",
  "encoding": "utf-8",
  "write_time": 0.0045
}
```

### Error Response

```json
{
  "status": "error",
  "file_path": "/etc/automax/config.yaml",
  "error": "Permission denied: /etc/automax/config.yaml",
  "details": "Cannot write to protected system directory"
}
```

## Troubleshooting

### Common Errors

- **`Permission denied`**: Insufficient permissions to write the file
  - Check file and directory permissions
  - Ensure user has write access to the target directory
  - Use appropriate user privileges or sudo if required

- **`File exists`**: File already exists when using `create_new` mode
  - Choose a different filename or use `overwrite` mode
  - Delete the existing file first if appropriate
  - Check for race conditions in concurrent operations

- **`Directory not found`**: Parent directories don't exist
  - Enable `create_dirs: true` to automatically create directories
  - Manually create the directory structure beforehand
  - Verify the directory path is correct

- **`Disk full`**: No space left on device
  - Check available disk space
  - Clean up temporary files or old logs
  - Use storage monitoring to prevent outages

- **`Encoding error`**: Unable to encode content with specified encoding
  - Verify the content is compatible with the chosen encoding
  - Use `utf-8` for maximum compatibility
  - Check for invalid characters in the content

- **`Invalid file path`**: Malformed or invalid file path
  - Check for illegal characters in file path
  - Verify path length limits for the operating system
  - Use absolute paths for reliability

### Write Modes

- `overwrite`: Replace existing file content (default)
- `append`: Add content to the end of existing file
- `create_new`: Only write if file doesn't exist (fails if file exists)

### Best Practices

1. Always validate file paths before writing
2. Use appropriate encoding for the content type
3. Implement proper error handling for file operations
4. Use atomic writes for critical configuration files
5. Set appropriate file permissions for sensitive data
6. Monitor disk space to prevent write failures
7. Use temporary files for large writes to avoid corruption

### Security Considerations

- Validate and sanitize all file paths to prevent directory traversal attacks
- Set appropriate file permissions for sensitive data
- Avoid writing to system directories without proper privileges
- Be cautious when writing files based on user input
- Use secure temporary file handling
- Implement proper file locking for concurrent access

### Performance Tips

- Use buffered writes for large content
- Avoid frequent small writes to the same file
- Use appropriate chunk sizes for optimal I/O performance
- Consider compression for large text files
- Monitor I/O performance for high-frequency write operations
