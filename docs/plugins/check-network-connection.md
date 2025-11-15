# Network Check Plugin

Check network connectivity to a host and port.

## Configuration

**Required:**
- `host`: Target host

**Optional:**
- `port`: Target port (default: 80)
- `timeout`: Connection timeout in seconds (default: 5)
- `fail_fast`: Raise error on failure (default: true)

## Example

```yaml
plugin: check_network_connection
config:
  host: "google.com"
  port: 443
  timeout: 10
```
