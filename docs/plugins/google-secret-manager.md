# Google Secret Manager Plugin

Retrieve secrets from Google Cloud Secret Manager.

## Configuration

**Required:**
- `project_id`: GCP project ID
- `secret_name`: Secret identifier
- `action`: Operation - "read", "write", "create", "add_version"

**Optional:**
- `value`: Secret value for write/add_version operations
- `key_file_path`: Path to service account key file

## Example

```yaml
plugin: google_secret_manager
config:
  project_id: "my-project"
  secret_name: "my-secret"
  action: "read"
```

## Supported Actions

- **read**: Read the latest version of a secret
- **write**: Write a new version of a secret (requires `value`)
- **create**: Create a new secret (requires `value`)
- **add_version**: Add a new version to an existing secret (requires `value`)

## Return Values

The plugin returns a dictionary with:
- `status`: "success", "created", "version_added", or "failure"
- `project_id`: The GCP project ID
- `secret_name`: The secret name
- `value`: The secret value (for read) or the written value (for write/add_version)
- `version_id`: The version ID (for read, defaults to "latest")
- `version_name`: The full version name (for write/add_version)
