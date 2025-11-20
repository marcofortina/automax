# AWS Secrets Manager Plugin

Retrieve secrets from AWS Secrets Manager.

## Description

This plugin allows you to retrieve, create, and update secrets stored in AWS Secrets Manager. It supports both string and binary secrets, and can handle JSON-formatted secrets automatically.

## Configuration

### Required Parameters

- `secret_name` (string): The name or ARN of the secret to retrieve
- `action` (string): Operation to perform - `read`, `write`, or `create`

### Optional Parameters

- `region_name` (string): AWS region name (default: us-east-1)
- `profile_name` (string): AWS profile name to use
- `value` (string): Secret value for write/create actions

## Examples

### Read a Secret

```yaml
- name: get_database_credentials
  plugin: aws_secrets_manager
  parameters:
    secret_name: "prod/database/credentials"
    action: "read"
    region_name: "us-east-1"
```

### Read a Secret with Specific Profile

```yaml
- name: get_api_key
  plugin: aws_secrets_manager
  parameters:
    secret_name: "api/keys/service"
    action: "read"
    region_name: "eu-west-1"
    profile_name: "production"
```

### Create a New Secret

```yaml
- name: create_new_secret
  plugin: aws_secrets_manager
  parameters:
    secret_name: "new/application/secret"
    action: "create"
    value: "my-secret-value"
    region_name: "us-west-2"
```

### Update an Existing Secret

```yaml
- name: update_secret
  plugin: aws_secrets_manager
  parameters:
    secret_name: "existing/secret"
    action: "write"
    value: "updated-secret-value"
```

## Return Values

### Read Action

```json
{
  "status": "success",
  "secret_name": "prod/database/credentials",
  "action": "read",
  "value": "{\"username\":\"admin\",\"password\":\"secret123\"}",
  "version_id": "v1"
}
```

### Write/Create Action

```json
{
  "status": "created",
  "secret_name": "new/application/secret",
  "action": "create",
  "value": "my-secret-value",
  "version_id": "v2"
}
```

## Troubleshooting

### Common Errors

- **`ResourceNotFoundException`**: The specified secret doesn't exist
  - Verify the secret name and region
  - Check if you have permissions to access the secret

- **`AccessDeniedException`**: Insufficient permissions
  - Ensure your AWS credentials have `secretsmanager:GetSecretValue` permission
  - Verify the IAM role or user has appropriate access

- **`NoCredentialsError`**: AWS credentials not found
  - Configure AWS credentials using AWS CLI or environment variables
  - Check if the profile exists if using `profile_name`

- **`DecryptionFailure`**: Unable to decrypt the secret
  - Verify the KMS key is accessible and properly configured
  - Check encryption permissions

### Best Practices

1. Use meaningful secret names with path-like structure (e.g., `environment/service/secret`)
2. Always handle secrets securely and avoid logging them
3. Use IAM roles instead of access keys when possible
4. Regularly rotate secrets and update accordingly

## Required AWS Permissions

### Read Secrets
```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue",
    "secretsmanager:DescribeSecret"
  ],
  "Resource": "*"
}
```

### Write/Create Secrets
```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:CreateSecret",
    "secretsmanager:PutSecretValue",
    "secretsmanager:UpdateSecret"
  ],
  "Resource": "*"
}
```
