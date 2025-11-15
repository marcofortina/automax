# Plugins Overview

Automax plugins are the building blocks of your automation workflows.
Each plugin performs a specific task and can be combined to create complex workflows.

## Plugin Categories

### Cloud Integration
- **AWS Secrets Manager**: Retrieve secrets from AWS Secrets Manager
- **Azure Key Vault**: Access secrets from Azure Key Vault
- **Google Secret Manager**: Get secrets from GCP Secret Manager
- **HashiCorp Vault**: Integrate with HashiCorp Vault

### System Operations
- **Local Command**: Execute local system commands
- **SSH Command**: Run commands on remote servers via SSH
- **Network Check**: Verify network connectivity

### File Operations
- **Read File**: Read content from files
- **Write File**: Write content to files
- **Compress File**: Compress files and directories
- **Uncompress File**: Extract compressed archives

### Communication
- **HTTP Request**: Make HTTP API calls
- **Email**: Send email notifications

### Database
- **Database Operations**: Execute SQL queries and operations

## Using Plugins

Plugins are configured in your workflow YAML files:

```yaml
steps:
  - name: "get_database_password"
    plugin: "aws_secrets_manager"
    config:
      secret_name: "production/database/password"
      region_name: "us-east-1"
```

## Creating Custom Plugins

See the [Creating Plugins](../guides/creating-plugins.md) guide for instructions
on developing your own plugins.