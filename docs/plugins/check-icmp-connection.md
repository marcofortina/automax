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

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `host`: The target host
- `count`: The number of ping packets sent
- `timeout`: The timeout per packet
- `interval`: The interval between packets
- `connected`: Boolean indicating if the host is reachable
- `packet_loss`: Percentage of packet loss
- `rtt_avg_ms`: Average round-trip time in milliseconds
- `rtt_min_ms`: Minimum round-trip time in milliseconds
- `rtt_max_ms`: Maximum round-trip time in milliseconds
- `success_rate`: Percentage of successful packets
- `error`: Error message if applicable
