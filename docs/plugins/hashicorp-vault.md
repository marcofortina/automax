# HashiCorp Vault Plugin

Manage secrets in HashiCorp Vault.

## Description

This plugin enables secure storage and retrieval of secrets from HashiCorp Vault. It supports reading, writing, and creating secrets using various authentication methods including token-based auth and AppRole.

## Configuration

### Required Parameters

- `vault_url` (string): The URL of your HashiCorp Vault server
- `secret_path` (string): Path to the secret in Vault
- `action` (string): Operation to perform - `read`, `write`, or `create`

### Optional Parameters

- `vault_token` (string): Vault token for authentication
- `role_id` (string): Role ID for AppRole authentication
- `secret_id` (string): Secret ID for AppRole authentication
- `value` (string): Secret value for write/create actions (as JSON string)
- `mount_point` (string): Secrets engine mount point (default: secret)

## Examples

### Read a Secret using Token Authentication

```yaml
- name: get_database_credentials
  plugin: hashicorp_vault
  parameters:
    vault_url: "https://vault.example.com:8200"
    secret_path: "database/creds/production"
    action: "read"
    vault_token: "s.xxxxxxxxxxxxxxxx"
```

### Read a Secret using AppRole Authentication

```yaml
- name: get_api_secret
  plugin: hashicorp_vault
  parameters:
    vault_url: "https://vault.example.com:8200"
    secret_path: "api/keys/service"
    action: "read"
    role_id: "12345678-1234-1234-1234-123456789012"
    secret_id: "87654321-4321-4321-4321-210987654321"
```

### Create a New Secret

```yaml
- name: create_application_secret
  plugin: hashicorp_vault
  parameters:
    vault_url: "https://vault.example.com:8200"
    secret_path: "applications/myapp"
    action: "create"
    vault_token: "s.xxxxxxxxxxxxxxxx"
    value: '{"username": "app-user", "password": "secret123"}'
```

### Update a Secret

```yaml
- name: update_secret
  plugin: hashicorp_vault
  parameters:
    vault_url: "https://vault.example.com:8200"
    secret_path: "existing/secret"
    action: "write"
    vault_token: "s.xxxxxxxxxxxxxxxx"
    value: '{"new_key": "new_value"}'
```

### Read from Different Secrets Engine

```yaml
- name: get_kv2_secret
  plugin: hashicorp_vault
  parameters:
    vault_url: "https://vault.example.com:8200"
    secret_path: "my-secret"
    action: "read"
    vault_token: "s.xxxxxxxxxxxxxxxx"
    mount_point: "kv-v2"
```

## Return Values

### Read Action

```json
{
  "status": "success",
  "vault_url": "https://vault.example.com:8200",
  "secret_path": "database/creds/production",
  "action": "read",
  "data": {
    "username": "db-user",
    "password": "secret-password"
  },
  "metadata": {
    "version": 1,
    "created_time": "2023-01-01T00:00:00Z"
  }
}
```

### Write/Create Action

```json
{
  "status": "created",
  "vault_url": "https://vault.example.com:8200",
  "secret_path": "applications/myapp",
  "action": "create",
  "data": {
    "username": "app-user",
    "password": "secret123"
  }
}
```

## Troubleshooting

### Common Errors

- **`Permission denied`**: Insufficient permissions to access the secret
  - Verify the token or AppRole has the correct policies
  - Check if the secret path is accessible

- **`Secret not found`**: The specified secret doesn't exist
  - Verify the secret path and mount point
  - Check if the secret has been deleted or moved

- **`Missing authentication`**: No valid authentication method provided
  - Provide either `vault_token` or both `role_id` and `secret_id`
  - Ensure the token is valid and not expired

- **`Invalid secret path`**: Malformed secret path
  - Ensure the path follows Vault naming conventions
  - Avoid special characters except hyphens and underscores

- **`Missing 'value' for write/create action`**: No value provided for write operations
  - Ensure the `value` parameter is provided for write and create actions
  - Value must be a valid JSON string

- **`Invalid action`**: Unsupported action specified
  - Use only `read`, `write`, or `create` actions

### Authentication Methods

1. **Token Authentication**:
   - Provide `vault_token` parameter
   - Tokens can be created via Vault UI, CLI, or API

2. **AppRole Authentication**:
   - Provide both `role_id` and `secret_id`
   - Recommended for machine-to-machine authentication

3. **Environment Variables**:
   - Set `VAULT_TOKEN` environment variable
   - Automatically used if no authentication parameters provided

### Best Practices

1. Use meaningful secret paths with organizational structure
2. Implement secret rotation policies
3. Use AppRole for automated workflows
4. Set appropriate TTL for tokens
5. Use different mount points for different types of secrets
6. Regularly audit secret access patterns

## Required Vault Policies

### Read Secrets
```hcl
path "secret/data/*" {
  capabilities = ["read"]
}
```

### Write/Create Secrets
```hcl
path "secret/data/*" {
  capabilities = ["create", "update"]
}
```

### For Specific Path
```hcl
path "secret/data/database/*" {
  capabilities = ["read", "create", "update"]
}
```
