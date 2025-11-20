# SSH Command Plugin

Execute commands on remote servers via SSH.

## Description

This plugin enables executing commands on remote servers using SSH protocol. It supports password-based authentication, key-based authentication, and provides detailed output capture including stdout, stderr, and exit codes.

## Configuration

### Required Parameters

- `host` (string): Remote server hostname or IP address
- `username` (string): Username for SSH authentication
- `command` (string): Command to execute on the remote server

### Optional Parameters

- `port` (integer): SSH port number (default: 22)
- `password` (string): Password for authentication (if using password auth)
- `private_key_path` (string): Path to private key file (if using key-based auth)
- `private_key_string` (string): Private key as string (alternative to file path)
- `timeout` (integer): Connection timeout in seconds (default: 30)

## Examples

### Execute Command with Password Authentication

```yaml
- name: check_disk_usage
  plugin: ssh_command
  parameters:
    host: "server.example.com"
    username: "admin"
    password: "my-password"
    command: "df -h"
    timeout: 60
```

### Execute Command with Key-Based Authentication

```yaml
- name: restart_service
  plugin: ssh_command
  parameters:
    host: "prod-server.example.com"
    username: "deploy"
    private_key_path: "/home/user/.ssh/id_rsa"
    command: "sudo systemctl restart myapp"
    port: 2222
```

### Execute Command with Private Key String

```yaml
- name: deploy_application
  plugin: ssh_command
  parameters:
    host: "192.168.1.100"
    username: "deployer"
    private_key_string: "-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----"
    command: "cd /app && git pull && npm install"
```

### Execute Multiple Commands

```yaml
- name: system_health_check
  plugin: ssh_command
  parameters:
    host: "monitoring-server.com"
    username: "monitor"
    password: "secure-pass"
    command: "uptime && free -m && ps aux | grep myapp"
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "host": "server.example.com",
  "username": "admin",
  "command": "df -h",
  "stdout": "Filesystem      Size  Used Avail Use% Mounted on\\n/dev/sda1        20G  5.2G   14G  28% /",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 2.34
}
```

### Error Response

```json
{
  "status": "error",
  "host": "server.example.com",
  "username": "admin",
  "command": "invalid-command",
  "stdout": "",
  "stderr": "bash: invalid-command: command not found",
  "exit_code": 127,
  "execution_time": 1.12,
  "error": "Command failed with exit code 127"
}
```

## Troubleshooting

### Common Errors

- **`Authentication failed`**: Unable to authenticate with the remote server
  - Verify username and password/key are correct
  - Check if the user account is active and accessible
  - Ensure private key format is correct (PEM format)

- **`Connection timeout`**: Unable to establish SSH connection
  - Verify the host is reachable and SSH port is open
  - Check firewall rules and network connectivity
  - Increase timeout value for slow connections

- **`Host key verification failed`**: SSH host key mismatch
  - Verify the host key in known_hosts file
  - For automation, consider managing host keys explicitly

- **`Command not found`**: Remote command does not exist
  - Check the command path and availability on remote system
  - Use full paths for commands (e.g., `/usr/bin/docker` instead of `docker`)

- **`Permission denied`**: Insufficient permissions on remote system
  - Ensure the user has execute permissions for the command
  - Use `sudo` if required (but note it may need password or NOPASSWD setup)

### Best Practices

1. Use key-based authentication for better security
2. Always handle sensitive passwords/keys securely
3. Use timeouts to prevent hanging connections
4. Validate commands before execution
5. Use absolute paths for critical commands
6. Implement error handling for command failures

### Security Considerations

- Never hardcode passwords in YAML files
- Use environment variables or secret managers for credentials
- Regularly rotate SSH keys and passwords
- Limit user permissions on remote systems
- Use separate deployment users with restricted access
