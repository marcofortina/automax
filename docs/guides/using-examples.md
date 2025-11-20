# Using Examples Guide

Learn how to use Automax examples to accelerate your automation workflows.

## Overview

Automax provides two types of examples:
- **Basic Examples**: Simple, single-purpose workflows for learning
- **Advanced Examples**: Complex, real-world workflows for production

## Basic Examples

Located in `examples/basic/`, these examples are perfect for beginners:

### Running Basic Examples

```bash
# Run local commands example
automax run --config examples/config/config.yaml --steps basic/local-commands

# Run file operations example
automax run --config examples/config/config.yaml --steps basic/file-operations

# Run HTTP requests example
automax run --config examples/config/config.yaml --steps basic/http-requests

# Run network checks example
automax run --config examples/config/config.yaml --steps basic/network-checks

# Run SSH command example
automax run --config examples/config/config.yaml --steps basic/ssh-commands

# Run email example
automax run --config examples/config/config.yaml --steps basic/send-email

# Run database operations example
automax run --config examples/config/config.yaml --steps basic/database-operations
```

### Basic Examples Structure

Each basic example focuses on one plugin category:
- **Local Commands**: System information and file operations
- **File Operations**: Read, write, compress, and uncompress files
- **HTTP Requests**: API calls and web service interactions
- **Network Checks**: Connectivity and port testing
- **SSH Commands**: Execute commands on remote servers
- **Email**: Send email notifications
- **Database Operations**: Basic SQL queries and operations

## Advanced Examples

Located in `examples/advanced/`, these examples demonstrate complex workflows:

### Running Advanced Examples

```bash
# Run multi-cloud secrets management
automax run --config examples/config/config.yaml --steps advanced/multi-cloud-secrets

# Run CI/CD pipeline example
automax run --config examples/config/config.yaml --steps advanced/ci-cd-pipeline

# Run data processing workflow
automax run --config examples/config/config.yaml --steps advanced/data-processing

# Run monitoring alerts system
automax run --config examples/config/config.yaml --steps advanced/monitoring-alerts
```

### Advanced Examples Overview

#### Multi-Cloud Secrets Management
- Retrieves secrets from AWS, Azure, GCP, and HashiCorp Vault
- Creates consolidated configuration files
- Sends notification when complete

#### CI/CD Pipeline
- Automated testing and deployment
- Health checks and rollback readiness
- Multi-environment deployment

#### Data Processing
- ETL workflows with file operations
- Database integration and reporting
- Automated email notifications

#### Monitoring Alerts
- Comprehensive system health checks
- Conditional alerting based on thresholds
- Multi-channel notifications

## Customizing Examples

### Environment Variables
Most examples use environment variables for credentials:

```bash
export AWS_ACCESS_KEY_ID="your-key"
export AZURE_CLIENT_ID="your-client-id"
export DB_HOST="localhost"
```

### Configuration Adjustments
Modify example files to match your environment:

```yaml
# Change hosts and paths
parameters:
  host: "your-server.com"
  file_path: "/your/path/file.txt"
```

### Step Modification
Add, remove, or modify steps to suit your needs:

```yaml
# Add additional steps
- name: "custom_step"
  plugin: "local_command"
  parameters:
    command: "your-custom-command"
```

## Best Practices for Using Examples

1. **Start with Basic Examples**: Understand fundamental concepts first
2. **Review Parameters**: Check all parameters match your environment
3. **Test in Dry-Run Mode**: Validate without execution
4. **Use Version Control**: Track changes to examples
5. **Security First**: Never commit real credentials to examples

## Troubleshooting

### Common Issues

**Example not found**:
- Verify the example path is correct
- Check the examples directory structure

**Permission errors**:
- Ensure file paths are accessible
- Check SSH key permissions

**Connection timeouts**:
- Verify network connectivity
- Adjust timeout parameters

**Authentication failures**:
- Confirm credentials are set correctly
- Check service permissions

### Getting Help

- Review plugin-specific documentation
- Check the [troubleshooting sections](../plugins/index.md) in plugin docs
- Open an issue on GitHub with your specific error

## Next Steps

After mastering the examples:
1. [Create your own workflows](creating-plugins.md)
2. [Explore output mapping](output-mapping.md)
3. [Learn about templating](templating.md)
4. [Browse all plugins](../plugins/index.md)
