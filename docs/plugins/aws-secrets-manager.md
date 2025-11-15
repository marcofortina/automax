# AWS Secrets Manager Plugin

Retrieve secrets from AWS Secrets Manager.

## Configuration

**Required:**
- `secret_name`: Name of the secret to retrieve

**Optional:**
- `region_name`: AWS region (default: us-east-1)
- `profile_name`: AWS profile name
- `role_arn`: IAM role ARN for cross-account access

## Example

```yaml
plugin: aws_secrets_manager
config:
  secret_name: "my-database-password"
  region_name: "eu-west-1"
```
