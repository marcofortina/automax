# TCP Check Plugin

Check TCP connectivity to a host and port.

## Configuration

**Required:**
- `host`: Target host
- `port`: Target port

**Optional:**
- `timeout`: Connection timeout in seconds (default: 5)
- `fail_fast`: Raise error on failure (default: true)

## Example

```yaml
plugin: check_tcp_connection
config:
  host: "google.com"
  port: 443
  timeout: 10
```