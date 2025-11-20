# Local Command Plugin

Execute commands on the local system.

## Description

This plugin enables executing shell commands on the local machine where Automax is running. It provides detailed output capture including stdout, stderr, exit codes, and execution time metrics.

## Configuration

### Required Parameters

- `command` (string): Command to execute on the local system

### Optional Parameters

- `working_directory` (string): Working directory for command execution
- `timeout` (integer): Command execution timeout in seconds (default: 300)
- `environment` (object): Environment variables as key-value pairs
- `shell` (boolean): Use shell execution (default: true)

## Examples

### Execute Simple System Command

```yaml
- name: check_system_info
  plugin: local_command
  parameters:
    command: "uname -a && whoami"
```

### Execute Command with Working Directory

```yaml
- name: list_project_files
  plugin: local_command
  parameters:
    command: "ls -la"
    working_directory: "/home/user/projects/automax"
```

### Execute Command with Environment Variables

```yaml
- name: build_application
  plugin: local_command
  parameters:
    command: "echo $BUILD_ENV && npm run build"
    working_directory: "/app"
    environment:
      BUILD_ENV: "production"
      NODE_ENV: "production"
    timeout: 600
```

### Execute Command with Timeout

```yaml
- name: long_running_process
  plugin: local_command
  parameters:
    command: "python long_script.py"
    timeout: 3600
```

### Execute Pipeline Commands

```yaml
- name: system_health_check
  plugin: local_command
  parameters:
    command: "ps aux | grep automax | wc -l"
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "command": "ls -la",
  "working_directory": "/home/user/projects",
  "stdout": "total 128\ndrwxr-xr-x 12 user user  4096 Jan  1 12:00 .\ndrwxr-xr-x  5 user user  4096 Jan  1 11:30 ..",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.123
}
```

### Error Response

```json
{
  "status": "error",
  "command": "invalid_command",
  "working_directory": "/home/user",
  "stdout": "",
  "stderr": "bash: invalid_command: command not found",
  "exit_code": 127,
  "execution_time": 0.045,
  "error": "Command failed with exit code 127"
}
```

### Timeout Response

```json
{
  "status": "error",
  "command": "sleep 100",
  "stdout": "",
  "stderr": "",
  "exit_code": null,
  "execution_time": 30.0,
  "error": "Command timed out after 30 seconds"
}
```

## Troubleshooting

### Common Errors

- **`Command not found`**: The specified command doesn't exist
  - Verify the command is installed and available in PATH
  - Use full paths for commands (e.g., `/usr/bin/python3` instead of `python3`)
  - Check command spelling and syntax

- **`Permission denied`**: Insufficient permissions to execute command
  - Ensure the user has execute permissions for the command
  - Check file permissions and ownership
  - Run as appropriate user or use sudo (if configured for passwordless execution)

- **`Timeout`**: Command execution timed out
  - Increase timeout value for long-running commands
  - Optimize command performance or split into smaller commands
  - Check system resources (CPU, memory, disk I/O)

- **`Working directory not found`**: Specified directory doesn't exist
  - Verify the working directory path exists
  - Check directory permissions
  - Use absolute paths for reliability

- **`Invalid environment variables`**: Malformed environment configuration
  - Ensure environment keys are valid (no spaces, special characters)
  - Verify values are properly formatted

### Best Practices

1. Use absolute paths for commands and working directories
2. Implement proper error handling for command failures
3. Set appropriate timeouts for different types of commands
4. Validate and sanitize command inputs to prevent injection attacks
5. Use environment variables for configuration instead of hardcoded values
6. Monitor command execution times for performance optimization
7. Implement retry logic for transient failures

### Security Considerations

- Never execute untrusted or user-provided commands
- Validate all command parameters before execution
- Use principle of least privilege for command execution
- Avoid executing commands with elevated privileges unless necessary
- Log command execution for audit purposes
- Sanitize environment variables to prevent injection

### Common Use Cases

- **System administration**: Package updates, service management
- **File operations**: Copy, move, delete files
- **Build processes**: Compilation, testing, packaging
- **Deployment scripts**: Application deployment, configuration
- **Monitoring**: System health checks, log analysis
- **Data processing**: ETL jobs, file conversion
