# Google Secret Manager Plugin

Retrieve secrets from Google Cloud Secret Manager.

## Configuration

**Required:**
- `project_id`: GCP project ID
- `secret_id`: Secret identifier

**Optional:**
- `version_id`: Secret version (default: latest)

## Example

```yaml
plugin: google_secret_manager
config:
  project_id: "my-gcp-project"
  secret_id: "database-credentials"
```
