# SSH Command Plugin

Execute commands on remote servers via SSH.

## Configuration

**Required:**
- `host`: Remote host
- `command`: Command to execute

**Optional:**
- `port`: SSH port (default: 22)
- `username`: SSH username (default: root)
- `password`: SSH password
- `key_file`: SSH private key file
- `timeout`: Connection timeout in seconds (default: 30)

## Example

```yaml
plugin: ssh_command
config:
  host: "server.example.com"
  command: "ls -la /opt"
  username: "deploy"
  key_file: "/home/user/.ssh/id_rsa"
```
