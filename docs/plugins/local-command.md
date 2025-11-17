# Local Command Plugin

Execute local system commands.

## Configuration

**Required:**
- `command`: Command to execute

**Optional:**
- `timeout`: Command timeout in seconds (default: 30)
- `shell`: Use shell execution (default: true)
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

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `command`: The executed command
- `returncode`: The exit code of the command
- `stdout`: The standard output of the command
- `stderr`: The standard error of the command
- `timeout`: The timeout setting
- `shell`: The shell setting
