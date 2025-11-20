# Compress File Plugin

Compress files and directories using various compression algorithms.

## Description

This plugin enables compressing files and directories into archive formats like ZIP, TAR.GZ, and TAR.BZ2. It supports both single files and multiple files/directories with flexible compression options.

## Configuration

### Required Parameters

- `source_path` (string|array): Path(s) to the file(s) or directory to compress
- `output_path` (string): Path for the output compressed file

### Optional Parameters

- `compression_type` (string): Compression format - `zip`, `tar.gz`, `tar.bz2` (default: zip)
- `include_pattern` (string): Pattern to include files (e.g., `*.log`)
- `exclude_pattern` (string): Pattern to exclude files (e.g., `*.tmp`)
- `compression_level` (integer): Compression level (1-9, default: 6)
- `preserve_paths` (boolean): Preserve full directory structure (default: true)

## Examples

### Compress Single File to ZIP

```yaml
- name: compress_log_file
  plugin: compress_file
  parameters:
    source_path: "/var/log/application.log"
    output_path: "/backup/application.log.zip"
    compression_type: "zip"
    compression_level: 9
```

### Compress Directory to TAR.GZ

```yaml
- name: backup_website
  plugin: compress_file
  parameters:
    source_path: "/var/www/html"
    output_path: "/backup/website-$(date +%Y%m%d).tar.gz"
    compression_type: "tar.gz"
    compression_level: 6
    preserve_paths: true
```

### Compress Multiple Files

```yaml
- name: compress_logs
  plugin: compress_file
  parameters:
    source_path:
      - "/var/log/app1.log"
      - "/var/log/app2.log"
      - "/var/log/app3.log"
    output_path: "/backup/all_logs.zip"
    compression_type: "zip"
```

### Compress with File Patterns

```yaml
- name: compress_source_code
  plugin: compress_file
  parameters:
    source_path: "/home/user/project"
    output_path: "/backup/project_source.tar.bz2"
    compression_type: "tar.bz2"
    include_pattern: "*.py"
    exclude_pattern: "*.pyc"
    compression_level: 8
```

### Compress with Minimal Compression

```yaml
- name: quick_archive
  plugin: compress_file
  parameters:
    source_path: "/tmp/data"
    output_path: "/tmp/data.zip"
    compression_type: "zip"
    compression_level: 1
    preserve_paths: false
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "source_path": ["/var/log/app1.log", "/var/log/app2.log"],
  "output_path": "/backup/logs.zip",
  "compression_type": "zip",
  "original_size": 10485760,
  "compressed_size": 2097152,
  "compression_ratio": 0.2,
  "file_count": 2,
  "compression_time": 3.45
}
```

### Error Response

```json
{
  "status": "error",
  "source_path": "/nonexistent/file.txt",
  "output_path": "/backup/archive.zip",
  "error": "Source file not found: /nonexistent/file.txt",
  "details": "Please verify the source path exists"
}
```

## Troubleshooting

### Common Errors

- **`Source not found`**: Source file or directory doesn't exist
  - Verify the source path is correct
  - Check if files have been moved or deleted
  - Ensure the user has read access to source files

- **`Permission denied`**: Insufficient permissions to read source or write output
  - Check file and directory permissions
  - Ensure user has read access to source and write access to output directory
  - Use appropriate user privileges if required

- **`Output path exists`**: Output file already exists
  - Choose a different output filename
  - Delete the existing file first if appropriate
  - Use unique names with timestamps or version numbers

- **`Unsupported compression type`**: Invalid compression format specified
  - Use only supported formats: `zip`, `tar.gz`, `tar.bz2`
  - Check spelling and case sensitivity

- **`Compression failed`**: Error during compression process
  - Check available disk space for temporary files
  - Verify source files are not corrupted
  - Try lower compression level for problematic files

- **`Empty source`**: No files found to compress
  - Verify source path contains files
  - Check if include/exclude patterns are too restrictive
  - Ensure file patterns match the actual files

### Compression Types

- `zip`: ZIP format (good for Windows compatibility)
- `tar.gz`: Gzip compressed tar (good for Unix/Linux, better compression)
- `tar.bz2`: Bzip2 compressed tar (better compression, slower)

### Compression Levels

- `1`: Fastest compression, largest file size
- `6`: Default balance between speed and size
- `9`: Best compression, slowest speed

### Best Practices

1. Use appropriate compression type for the target platform
2. Choose compression level based on needs (speed vs size)
3. Include timestamps in output filenames for backups
4. Verify compressed archives after creation
5. Monitor disk space during compression of large files
6. Use file patterns to include/exclude specific file types
7. Consider splitting very large archives

### Performance Considerations

- Higher compression levels use more CPU and time
- Compression works best on text-based files
- Already compressed files (images, videos) see little benefit
- Use lower compression for frequently created archives
- Consider solid compression for groups of similar files

### Use Cases

- **Backup operations**: Compress logs, databases, configurations
- **Data transfer**: Reduce size for network transfer
- **Archiving**: Long-term storage of old data
- **Distribution**: Package applications or data for distribution
- **Space optimization**: Free up disk space by compressing old files
