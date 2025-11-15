# HashiCorp Vault Plugin

Retrieve secrets from HashiCorp Vault.

## Configuration

**Required:**
- `vault_url`: Vault server URL
- `secret_path`: Path to the secret

**Optional:**
- `token`: Vault authentication token
- `engine`: Secrets engine (default: secret)
- `timeout`: Request timeout in seconds (default: 30)

## Example

```yaml
plugin: hashicorp_vault
config:
  vault_url: "https://vault.example.com"
  secret_path: "database/creds"
  token: "s.1234567890"
```
