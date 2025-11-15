# Uncompress File Plugin

Extract compressed files and archives.

## Configuration

**Required:**
- `source_path`: Source archive file
- `output_path`: Output directory

**Optional:**
- `format`: Compression format - gzip, tar, zip (auto-detected)

## Example

```yaml
plugin: uncompress_file
config:
  source_path: "/backup/data.zip"
  output_path: "/tmp/extracted"
```
