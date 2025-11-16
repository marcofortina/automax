# ICMP Check Plugin

Check ICMP connectivity to a host.

## Configuration

**Required:**
- `host`: Target host

**Optional:**
- `count`: Number of ping packets (default: 4)
- `timeout`: Timeout in seconds for each packet (default: 2)
- `interval`: Interval between packets in seconds (default: 0.2)
- `fail_fast`: Raise error on failure (default: true)

## Example

```yaml
plugin: check_icmp_connection
config:
  host: "google.com"
  count: 5
  timeout: 3
  interval: 0.5
  fail_fast: false
```
