# Google Secret Manager Plugin

Manage secrets in Google Cloud Secret Manager.

## Description

This plugin enables secure storage and retrieval of secrets from Google Cloud Secret Manager. It supports reading, writing, and creating secrets using various authentication methods including service account credentials and default application credentials.

## Configuration

### Required Parameters

- `project_id` (string): The GCP project ID containing the secret
- `secret_id` (string): The ID of the secret to access
- `action` (string): Operation to perform - `read`, `write`, or `create`

### Optional Parameters

- `credentials_path` (string): Path to GCP service account credentials JSON file
- `version_id` (string): Specific version of the secret (default: latest)
- `value` (string): Secret value for write/create actions

## Examples

### Read a Secret Using Default Credentials

```yaml
- name: get_database_password
  plugin: google_secret_manager
  parameters:
    project_id: "my-gcp-project"
    secret_id: "database-password"
    action: "read"
```

### Read a Secret with Service Account

```yaml
- name: get_api_key
  plugin: google_secret_manager
  parameters:
    project_id: "production-project"
    secret_id: "api-key"
    action: "read"
    credentials_path: "/path/to/service-account.json"
```

### Read a Specific Secret Version

```yaml
- name: get_previous_secret_version
  plugin: google_secret_manager
  parameters:
    project_id: "my-gcp-project"
    secret_id: "database-password"
    action: "read"
    version_id: "2"
```

### Create a New Secret

```yaml
- name: create_application_secret
  plugin: google_secret_manager
  parameters:
    project_id: "my-gcp-project"
    secret_id: "new-application-secret"
    action: "create"
    value: "very-secret-value"
```

### Update a Secret

```yaml
- name: update_secret
  plugin: google_secret_manager
  parameters:
    project_id: "my-gcp-project"
    secret_id: "existing-secret"
    action: "write"
    value: "updated-secret-value"
```

## Return Values

### Read Action

```json
{
  "status": "success",
  "project_id": "my-gcp-project",
  "secret_id": "database-password",
  "secret_value": "my-password",
  "version_id": "1",
  "action": "read"
}
```

### Write/Create Action

```json
{
  "status": "created",
  "project_id": "my-gcp-project",
  "secret_id": "new-secret",
  "secret_value": "very-secret-value",
  "action": "create"
}
```

## Troubleshooting

### Common Errors

- **`PermissionDenied`**: Insufficient permissions to access the secret
  - Verify the service account has `secretmanager.secrets.accessor` role
  - Check if the secret exists in the specified project

- **`NotFound`**: The specified secret doesn't exist
  - Verify the secret ID and project ID
  - Check if the secret has been deleted

- **`InvalidArgument`**: Invalid secret name or version
  - Ensure secret IDs only contain letters, numbers, hyphens, and underscores
  - Verify version format (e.g., "latest" or numeric version)

- **`Authentication failed`**: Unable to authenticate with GCP
  - Verify service account credentials file exists and is valid
  - Check `GOOGLE_APPLICATION_CREDENTIALS` environment variable if using default credentials

- **`Missing 'value' for write/create action`**: No value provided for write operations
  - Ensure the `value` parameter is provided for write and create actions

- **`Invalid action`**: Unsupported action specified
  - Use only `read`, `write`, or `create` actions

### Authentication Methods

1. **Default Application Credentials** (Recommended for GCP resources):
   - No additional configuration needed
   - Automatically uses the service account attached to the resource

2. **Service Account Credentials File**:
   - Provide `credentials_path` parameter
   - Ensure the service account has Secret Manager access

3. **Environment Variable**:
   - Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
   - Points to service account JSON key file

## Required GCP Permissions

### Secret Manager Secret Accessor
- `secretmanager.versions.access`
- `secretmanager.secrets.get`

### Secret Manager Admin
- `secretmanager.secrets.create`
- `secretmanager.versions.add`
- `secretmanager.secrets.update`
