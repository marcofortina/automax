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
  fail_fast: true
```

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `host`: The target host
- `port`: The target port
- `timeout`: The connection timeout
- `connected`: Boolean indicating if the connection was successful
- `error`: Error message if applicable
