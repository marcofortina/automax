# Read File Content Plugin

Read and retrieve content from files on the local filesystem.

## Description

This plugin enables reading content from various types of files including text files, JSON, XML, and binary files. It supports different encoding formats and provides flexible output handling.

## Configuration

### Required Parameters

- `file_path` (string): Path to the file to read

### Optional Parameters

- `encoding` (string): File encoding (default: utf-8)
- `as_bytes` (boolean): Return content as bytes instead of string (default: false)
- `max_size` (integer): Maximum file size to read in bytes (default: 10485760 = 10MB)

## Examples

### Read Text File

```yaml
- name: read_config_file
  plugin: read_file_content
  parameters:
    file_path: "/etc/automax/config.yaml"
    encoding: "utf-8"
```

### Read JSON File

```yaml
- name: read_package_json
  plugin: read_file_content
  parameters:
    file_path: "/app/package.json"
    encoding: "utf-8"
```

### Read File with Different Encoding

```yaml
- name: read_windows_file
  plugin: read_file_content
  parameters:
    file_path: "C:\\Users\\Admin\\file.txt"
    encoding: "utf-16"
```

### Read Binary File

```yaml
- name: read_binary_file
  plugin: read_file_content
  parameters:
    file_path: "/tmp/image.png"
    as_bytes: true
```

### Read File with Size Limit

```yaml
- name: read_large_file
  plugin: read_file_content
  parameters:
    file_path: "/var/log/app.log"
    max_size: 5242880
```

## Return Values

### Success Response (Text File)

```json
{
  "status": "success",
  "file_path": "/etc/automax/config.yaml",
  "content": "database:\n  host: localhost\n  port: 5432\n  name: automax",
  "encoding": "utf-8",
  "size": 65,
  "read_time": 0.0023
}
```

### Success Response (Binary File)

```json
{
  "status": "success",
  "file_path": "/tmp/image.png",
  "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "encoding": "base64",
  "size": 1024,
  "read_time": 0.0015
}
```

### Error Response

```json
{
  "status": "error",
  "file_path": "/nonexistent/file.txt",
  "content": null,
  "error": "File not found: /nonexistent/file.txt"
}
```

## Troubleshooting

### Common Errors

- **`File not found`**: The specified file doesn't exist
  - Verify the file path is correct
  - Check if the file has been moved or deleted
  - Ensure path uses correct forward/backward slashes for the OS

- **`Permission denied`**: Insufficient permissions to read the file
  - Check file permissions and ownership
  - Ensure the user has read access to the file
  - Verify directory permissions in the file path

- **`File too large`**: File exceeds maximum size limit
  - Increase `max_size` parameter for larger files
  - Consider processing the file in chunks if very large
  - Use streaming approaches for extremely large files

- **`Encoding error`**: Unable to decode file with specified encoding
  - Verify the file encoding matches the specified encoding
  - Try different encodings (utf-8, latin-1, utf-16, etc.)
  - Use `as_bytes: true` for binary files or unknown encodings

- **`Invalid file path`**: Malformed or invalid file path
  - Check for illegal characters in file path
  - Verify path length limits for the operating system
  - Ensure absolute paths are used when appropriate

- **`File in use`**: File is locked by another process
  - Check if another application has the file open
  - Wait and retry the operation
  - Use file locking mechanisms if available

### Supported Encodings

- `utf-8` (default): Universal character encoding
- `utf-16`: 16-bit Unicode encoding
- `latin-1`: ISO-8859-1 encoding
- `ascii`: Basic ASCII encoding
- `cp1252`: Windows-1252 encoding
- `iso-8859-1`: Latin-1 encoding

### Best Practices

1. Always validate file paths before reading
2. Use appropriate encoding for the file type
3. Set reasonable size limits to prevent memory issues
4. Handle binary files with `as_bytes: true` parameter
5. Implement error handling for file operations
6. Use absolute paths for reliability
7. Consider file locking for concurrent access scenarios

### Security Considerations

- Validate and sanitize all file paths to prevent directory traversal attacks
- Limit file access to authorized directories only
- Be cautious when reading files from user input or untrusted sources
- Set appropriate file size limits to prevent denial of service attacks
- Monitor file access patterns for suspicious activity
- Use secure temporary file handling when processing sensitive data

### Performance Tips

- For large files, consider streaming processing instead of loading entire file
- Use appropriate buffer sizes for optimal I/O performance
- Cache frequently accessed files when appropriate
- Monitor memory usage when processing multiple large files
- Use solid-state drives (SSD) for better I/O performance

### Common Use Cases

- **Configuration files**: Read application settings and parameters
- **Log files**: Analyze and process application logs
- **Data files**: Process CSV, JSON, XML data files
- **Templates**: Read and process template files
- **Certificates**: Read SSL/TLS certificates and keys
- **Documents**: Process text documents and reports
