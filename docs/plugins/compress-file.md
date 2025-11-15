# Compress File Plugin

Compress files and directories.

## Configuration

**Required:**
- `source_path`: Source file or directory
- `output_path`: Output archive path

**Optional:**
- `format`: Compression format - gzip, tar, zip (default: gzip)
- `compression_level`: Compression level 1-9 (default: 6)

## Example

```yaml
plugin: compress_file
config:
  source_path: "/data/logs"
  output_path: "/backup/logs.tar.gz"
  format: "tar"
```
