# Azure Key Vault Plugin

Retrieve secrets from Azure Key Vault.

## Configuration

**Required:**
- `vault_url`: URL of the Azure Key Vault
- `secret_name`: Name of the secret to retrieve
- `action`: Operation - "read", "write", "create"

**Optional:**
- `tenant_id`: Azure tenant ID
- `client_id`: Azure client ID
- `client_secret`: Azure client secret
- `value`: Secret value for write/create operations

## Example

```yaml
plugin: azure_key_vault
config:
  vault_url: "https://my-vault.vault.azure.net/"
  secret_name: "api-key"
  action: "read"
```

## Supported Actions

- **read**: Retrieve the secret value
- **write**: Write a secret (requires `value`)
- **create**: Create a secret (same as write, requires `value`)

## Return Values

The plugin returns a dictionary with:
- `status`: "success", "written", or "failure"
- `vault_url`: The Azure Key Vault URL
- `secret_name`: The name of the secret
- `secret_value`: The secret value (for read) or the written value (for write/create)
- `version`: The secret version (for read)
- `enabled`: Whether the secret is enabled (for read)
- `expires_on`: The expiration date of the secret (for read)
