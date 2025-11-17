# Compress File Plugin

Compress files and directories.

## Configuration

**Required:**
- `source_path`: Source file or directory
- `output_path`: Output archive path

**Optional:**
- `format`: Compression format - "gzip", "tar", "zip" (default: gzip)
- `compression_level`: Compression level 1-9 (default: 6)

## Example

```yaml
plugin: compress_file
config:
  source_path: "/data/logs"
  output_path: "/backup/logs.tar.gz"
  format: "tar"
  compression_level: 6
```

## Supported Formats

- **gzip**: Compress a single file using gzip
- **tar**: Create a tar archive of a directory
- **zip**: Create a zip archive of a directory

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `source_path`: The source path
- `output_path`: The output archive path
- `format`: The compression format used
- `original_size`: The original size in bytes
- `compressed_size`: The compressed size in bytes
