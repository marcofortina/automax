# AWS Secrets Manager Plugin

Retrieve secrets from AWS Secrets Manager.

## Configuration

**Required:**
- `secret_name`: Name of the secret to retrieve
- `action`: Operation - "read", "write", "create"

**Optional:**
- `region_name`: AWS region (default: us-east-1)
- `profile_name`: AWS profile name
- `role_arn`: IAM role ARN for cross-account access
- `value`: Secret value for write/create operations

## Example

```yaml
plugin: aws_secrets_manager
config:
  secret_name: "my-database-password"
  action: "read"
  region_name: "eu-west-1"
```

## Supported Actions

- **read**: Retrieve the secret value
- **write**: Update an existing secret (requires `value`)
- **create**: Create a new secret (requires `value`)

## Return Values

The plugin returns a dictionary with:
- `status`: "success", "updated", "created", or "failure"
- `secret_name`: The name of the secret
- `value`: The secret value (for read) or the written value (for write/create)
- `version_id`: The version ID of the secret (for read/write)
- `arn`: The Amazon Resource Name (ARN) of the secret (for create)
