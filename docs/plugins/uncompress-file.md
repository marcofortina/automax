# Uncompress File Plugin

Extract compressed files and archives.

## Configuration

**Required:**
- `source_path`: Source archive file
- `output_path`: Output directory or file

**Optional:**
- `format`: Compression format - "gzip", "tar", "zip" (auto-detected from file extension if not provided)

## Example

```yaml
plugin: uncompress_file
config:
  source_path: "/backup/data.zip"
  output_path: "/tmp/extracted"
  format: "zip"
```

## Supported Formats

- **gzip**: Extract a gzip file to a specified output file
- **tar**: Extract a tar archive to a directory
- **zip**: Extract a zip archive to a directory

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `source_path`: The source archive path
- `output_path`: The output path
- `format`: The compression format used
- `compressed_size`: The compressed size in bytes
- `extracted_size`: The extracted size in bytes (for gzip)
