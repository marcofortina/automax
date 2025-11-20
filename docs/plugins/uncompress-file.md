# Uncompress File Plugin

Extract files from compressed archives.

## Description

This plugin enables extracting files from various compressed archive formats including ZIP, TAR.GZ, TAR.BZ2, and more. It supports extraction to specified directories with options for preserving directory structure and handling existing files.

## Configuration

### Required Parameters

- `archive_path` (string): Path to the compressed archive file
- `output_dir` (string): Directory where files will be extracted

### Optional Parameters

- `preserve_paths` (boolean): Preserve full directory structure from archive (default: true)
- `overwrite` (boolean): Overwrite existing files (default: false)
- `password` (string): Password for encrypted archives (if required)
- `members` (array): Specific files to extract from archive (default: all files)

## Examples

### Extract ZIP Archive

```yaml
- name: extract_backup_zip
  plugin: uncompress_file
  parameters:
    archive_path: "/backup/website-20240101.zip"
    output_dir: "/tmp/extracted"
    preserve_paths: true
    overwrite: false
```

### Extract TAR.GZ Archive

```yaml
- name: extract_source_code
  plugin: uncompress_file
  parameters:
    archive_path: "/downloads/project-1.0.0.tar.gz"
    output_dir: "/opt/project"
    preserve_paths: true
    overwrite: true
```

### Extract Specific Files from Archive

```yaml
- name: extract_config_files
  plugin: uncompress_file
  parameters:
    archive_path: "/backup/full-backup.zip"
    output_dir: "/tmp/configs"
    members:
      - "etc/app/config.yaml"
      - "etc/app/secrets.json"
    preserve_paths: false
```

### Extract Password-Protected Archive

```yaml
- name: extract_encrypted_archive
  plugin: uncompress_file
  parameters:
    archive_path: "/secure/encrypted-backup.zip"
    output_dir: "/tmp/decrypted"
    password: "my-secret-password"
    overwrite: true
```

### Extract Without Preserving Paths

```yaml
- name: extract_flattened
  plugin: uncompress_file
  parameters:
    archive_path: "/data/files.tar.bz2"
    output_dir: "/tmp/flat"
    preserve_paths: false
    overwrite: false
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "archive_path": "/backup/website-20240101.zip",
  "output_dir": "/tmp/extracted",
  "extracted_files": [
    "/tmp/extracted/index.html",
    "/tmp/extracted/css/style.css",
    "/tmp/extracted/js/app.js"
  ],
  "file_count": 3,
  "extraction_time": 2.34,
  "total_size": 1048576
}
```

### Error Response

```json
{
  "status": "error",
  "archive_path": "/backup/corrupted.zip",
  "output_dir": "/tmp/extracted",
  "error": "Archive is corrupted or incomplete",
  "details": "Bad zip file"
}
```

## Troubleshooting

### Common Errors

- **`Archive not found`**: The specified archive file doesn't exist
  - Verify the archive path is correct
  - Check if the file has been moved or deleted
  - Ensure the user has read access to the archive

- **`Permission denied`**: Insufficient permissions to write to output directory
  - Check output directory permissions
  - Ensure user has write access to the target directory
  - Create the output directory beforehand if needed

- **`Output directory not found`**: Output directory doesn't exist
  - Create the output directory before extraction
  - Verify the directory path is correct
  - Use absolute paths for reliability

- **`Archive corrupted`**: The archive file is damaged or incomplete
  - Verify the archive was downloaded completely
  - Check for file corruption
  - Try downloading the archive again

- **`Password required`**: Archive is encrypted but no password provided
  - Provide the `password` parameter for encrypted archives
  - Verify the password is correct
  - Contact the archive creator for the password

- **`Unsupported format`**: Archive format not supported
  - Use supported formats: ZIP, TAR, TAR.GZ, TAR.BZ2
  - Convert the archive to a supported format
  - Check if the archive uses proprietary compression

- **`File exists`**: Output file already exists and overwrite is disabled
  - Enable `overwrite: true` to replace existing files
  - Remove existing files manually before extraction
  - Use a different output directory

### Supported Formats

- `zip`: ZIP archive format
- `tar`: Tape archive format (uncompressed)
- `tar.gz`: Gzip compressed tar archive
- `tar.bz2`: Bzip2 compressed tar archive
- `tar.xz`: XZ compressed tar archive

### Best Practices

1. Always verify archive integrity before extraction
2. Use temporary directories for extraction when possible
3. Implement proper cleanup after extraction
4. Handle password-protected archives securely
5. Validate extracted files for completeness
6. Monitor disk space during extraction of large archives
7. Use checksums to verify archive integrity

### Security Considerations

- Validate archive files from untrusted sources
- Scan extracted files for malware if from unknown sources
- Handle passwords securely (use environment variables or secret managers)
- Avoid extracting to system directories without proper privileges
- Set appropriate file permissions on extracted files
- Implement proper error handling for extraction failures
