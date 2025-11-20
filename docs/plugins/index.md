# Plugins Overview

Automax plugins are the building blocks of your automation workflows.
Each plugin performs a specific task and can be combined to create complex workflows.

## Plugin Categories

### Cloud Secrets Management
- [AWS Secrets Manager](aws-secrets-manager.md) - Retrieve, create, and update secrets from AWS Secrets Manager
- [Azure Key Vault](azure-key-vault.md) - Access secrets from Azure Key Vault using managed identity or service principal
- [Google Secret Manager](google-secret-manager.md) - Get secrets from GCP Secret Manager with service account or default credentials
- [HashiCorp Vault](hashicorp-vault.md) - Integrate with HashiCorp Vault using token or AppRole authentication

### System Operations
- [Local Command](local-command.md) - Execute local system commands with environment variables and working directory support
- [SSH Command](ssh-command.md) - Run commands on remote servers via SSH with password or key-based authentication

### File Operations
- [Read File Content](read-file-content.md) - Read content from files with support for multiple encodings and binary data
- [Write File Content](write-file-content.md) - Write content to files with overwrite, append, or create-new modes
- [Compress File](compress-file.md) - Compress files and directories to ZIP, TAR.GZ, or TAR.BZ2 formats
- [Uncompress File](uncompress-file.md) - Extract files from compressed archives with password support

### Network Operations
- [Check TCP Connection](check-tcp-connection.md) - Test TCP connectivity to remote hosts and ports
- [Check ICMP Connection](check-icmp-connection.md) - Test ICMP connectivity (ping) to remote hosts with latency metrics

### Communication
- [Run HTTP Request](run-http-request.md) - Make HTTP API calls with headers, authentication, and JSON support
- [Send Email](send-email.md) - Send email notifications via SMTP with HTML content and attachments

### Database
- [Database Operations](database-operations.md) - Execute SQL queries and operations on PostgreSQL, MySQL, SQLite, and Oracle databases

## Using Plugins

Plugins are configured in your workflow YAML files using the `parameters` section:

```yaml
steps:
  - name: "get_database_password"
    plugin: "aws_secrets_manager"
    parameters:
      secret_name: "production/database/password"
      region_name: "us-east-1"
      action: "read"
```

### Common Plugin Parameters

Most plugins support these common parameters:
- `action`: Operation to perform (read, write, create, execute, etc.)
- `timeout`: Operation timeout in seconds
- Authentication credentials specific to each service

### Error Handling

All plugins provide structured error responses:

```json
{
  "status": "error",
  "error": "Descriptive error message",
  "details": "Additional context for troubleshooting"
}
```

## Best Practices

1. **Use secrets management** for credentials and sensitive data
2. **Implement error handling** in your workflows
3. **Set appropriate timeouts** for network operations
4. **Validate inputs** before executing operations
5. **Use structured logging** for debugging and monitoring

## Plugin Examples

### Complete Workflow Example

```yaml
steps:
  - name: "get_api_credentials"
    plugin: "hashicorp_vault"
    parameters:
      vault_url: "https://vault.example.com"
      secret_path: "api/credentials"
      action: "read"
      vault_token: "${VAULT_TOKEN}"

  - name: "call_external_api"
    plugin: "run_http_request"
    parameters:
      url: "https://api.example.com/data"
      method: "GET"
      headers:
        Authorization: "Bearer ${steps.get_api_credentials.output.data.token}"
      timeout: 30

  - name: "save_results"
    plugin: "write_file_content"
    parameters:
      file_path: "/tmp/api_response.json"
      content: "${steps.call_external_api.output.body}"
      mode: "overwrite"

  - name: "send_notification"
    plugin: "send_email"
    parameters:
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      from_address: "automax@example.com"
      to_addresses: ["admin@example.com"]
      subject: "API Sync Completed"
      body: "External API data has been successfully retrieved and saved."
      username: "${EMAIL_USER}"
      password: "${EMAIL_PASSWORD}"
```

## Creating Custom Plugins

See the [Creating Plugins](../guides/creating-plugins.md) guide for instructions
on developing your own plugins.

## Troubleshooting

For plugin-specific issues, refer to the individual plugin documentation pages linked above. Each plugin documentation includes:
- Authentication and permission requirements
- Common error messages and solutions
- Configuration examples and best practices
- Network and connectivity requirements
