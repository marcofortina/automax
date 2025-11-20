# Azure Key Vault Plugin

Manage secrets in Azure Key Vault.

## Description

This plugin enables secure storage and retrieval of secrets from Azure Key Vault. It supports reading, writing, and creating secrets using various authentication methods including service principals and managed identities.

## Configuration

### Required Parameters

- `vault_url` (string): The URL of your Azure Key Vault
- `secret_name` (string): Name of the secret to access
- `action` (string): Operation to perform - `read`, `write`, or `create`

### Optional Parameters

- `tenant_id` (string): Azure tenant ID for service principal auth
- `client_id` (string): Client ID for service principal auth
- `client_secret` (string): Client secret for service principal auth
- `value` (string): Secret value for write/create actions

## Examples

### Read a Secret using Managed Identity

```yaml
- name: get_database_password
  plugin: azure_key_vault
  parameters:
    vault_url: "https://my-vault.vault.azure.net/"
    secret_name: "database-password"
    action: "read"
```

### Read a Secret using Service Principal

```yaml
- name: get_api_key
  plugin: azure_key_vault
  parameters:
    vault_url: "https://prod-vault.vault.azure.net/"
    secret_name: "api-key"
    action: "read"
    tenant_id: "12345678-1234-1234-1234-123456789012"
    client_id: "87654321-4321-4321-4321-210987654321"
    client_secret: "my-client-secret"
```

### Create a New Secret

```yaml
- name: create_application_secret
  plugin: azure_key_vault
  parameters:
    vault_url: "https://my-vault.vault.azure.net/"
    secret_name: "new-application-secret"
    action: "create"
    value: "very-secret-value"
```

### Update a Secret

```yaml
- name: update_secret
  plugin: azure_key_vault
  parameters:
    vault_url: "https://my-vault.vault.azure.net/"
    secret_name: "existing-secret"
    action: "write"
    value: "updated-secret-value"
```

## Return Values

### Read Action

```json
{
  "status": "success",
  "vault_url": "https://my-vault.vault.azure.net/",
  "secret_name": "database-password",
  "secret_value": "my-password",
  "version": "a1b2c3d4e5f6g7h8i9j0",
  "enabled": true,
  "expires_on": null
}
```

### Write/Create Action

```json
{
  "status": "written",
  "vault_url": "https://my-vault.vault.azure.net/",
  "secret_name": "new-secret",
  "secret_value": "very-secret-value",
  "action": "create"
}
```

## Troubleshooting

### Common Errors

- **`Secret not found`**: The specified secret doesn't exist
  - Verify the secret name and vault URL
  - Check if the secret has been deleted or disabled

- **`Vault authentication failed`**: Unable to authenticate with Azure
  - Verify your credentials or managed identity configuration
  - Check if the service principal has access to the key vault

- **`Missing 'value' for write/create action`**: No value provided for write operations
  - Ensure the `value` parameter is provided for write and create actions

- **`Invalid action`**: Unsupported action specified
  - Use only `read`, `write`, or `create` actions

### Authentication Methods

1. **Managed Identity** (Recommended for Azure resources):
   - No additional configuration needed
   - Automatically uses the system-assigned or user-assigned identity

2. **Service Principal**:
   - Provide `tenant_id`, `client_id`, and `client_secret`
   - Ensure the service principal has Key Vault access

3. **Azure CLI Credentials**:
   - Uses logged-in Azure CLI user context
   - Run `az login` before execution

## Required Azure Permissions

### Key Vault Secrets User
- `Microsoft.KeyVault/vaults/secrets/read`
- `Microsoft.KeyVault/vaults/secrets/get/action`

### Key Vault Secrets Officer
- `Microsoft.KeyVault/vaults/secrets/write`
- `Microsoft.KeyVault/vaults/secrets/set/action`
