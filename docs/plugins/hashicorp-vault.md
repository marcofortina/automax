# HashiCorp Vault Plugin

Retrieve secrets from HashiCorp Vault.

## Configuration

**Required:**
- `url`: Vault server URL
- `mount_point`: Secrets engine mount point
- `path`: Secret path
- `action`: Operation - "read", "write", "create"

**Optional:**
- `token`: Vault authentication token
- `namespace`: Vault namespace
- `value`: Secret value for write/create operations

## Example

```yaml
plugin: hashicorp_vault
config:
  url: "https://vault.example.com"
  mount_point: "secret"
  path: "my-app/credentials"
  action: "read"
  token: "s.1234567890"
```

## Supported Actions

- **read**: Read a secret from the specified path
- **write**: Write a secret to the specified path (requires `value`)
- **create**: Create a secret (same as write)

## Return Values

The plugin returns a dictionary with:
- `status`: "success", "written", or "failure"
- `mount_point`: The secrets engine mount point
- `path`: The secret path
- `action`: The performed action
- `value`: The secret value (for read) or the written value (for write/create)
- `version`: The secret version (for read)
- `created_time`: The creation time of the secret (for read)
