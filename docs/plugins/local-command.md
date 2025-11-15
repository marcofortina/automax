# Local Command Plugin

Execute local system commands.

## Configuration

**Required:**
- `command`: Command to execute

**Optional:**
- `timeout`: Command timeout in seconds (default: 30)
- `shell`: Use shell execution (default: false)
- `cwd`: Working directory
- `env`: Environment variables
- `input_data`: Input data for command

## Example

```yaml
plugin: local_command
config:
  command: "echo 'Hello World'"
  timeout: 10
  shell: true
```
