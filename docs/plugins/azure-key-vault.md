# Azure Key Vault Plugin

Retrieve secrets from Azure Key Vault.

## Configuration

**Required:**
- `vault_url`: URL of the Azure Key Vault
- `secret_name`: Name of the secret to retrieve

**Optional:**
- `tenant_id`: Azure tenant ID
- `client_id`: Azure client ID  
- `client_secret`: Azure client secret

## Example

```yaml
plugin: azure_key_vault
config:
  vault_url: "https://my-vault.vault.azure.net/"
  secret_name: "api-key"
```
