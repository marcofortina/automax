# Check ICMP Connection Plugin

Test ICMP connectivity to remote hosts (ping).

## Description

This plugin enables testing ICMP connectivity to specified hosts, commonly known as "ping". It's useful for verifying network reachability, measuring latency, and monitoring host availability.

## Configuration

### Required Parameters

- `host` (string): Target hostname or IP address

### Optional Parameters

- `count` (integer): Number of ping attempts (default: 3)
- `timeout` (integer): Timeout for each ping attempt in seconds (default: 5)
- `packet_size` (integer): Size of ICMP packet in bytes (default: 56)
- `interval` (float): Interval between pings in seconds (default: 1.0)

## Examples

### Basic ICMP Ping Test

```yaml
- name: ping_google
  plugin: check_icmp_connection
  parameters:
    host: "google.com"
    count: 4
    timeout: 3
```

### Ping with Custom Packet Size

```yaml
- name: ping_with_large_packets
  plugin: check_icmp_connection
  parameters:
    host: "192.168.1.1"
    count: 5
    packet_size: 1024
    interval: 0.5
```

### Ping Local Network Device

```yaml
- name: ping_router
  plugin: check_icmp_connection
  parameters:
    host: "192.168.1.254"
    timeout: 2
    count: 3
```

### Quick Ping Test

```yaml
- name: quick_ping
  plugin: check_icmp_connection
  parameters:
    host: "example.com"
    count: 1
    timeout: 1
```

### Extended Ping Test

```yaml
- name: extended_ping_test
  plugin: check_icmp_connection
  parameters:
    host: "server.example.com"
    count: 10
    interval: 0.2
    timeout: 10
    packet_size: 512
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "host": "google.com",
  "reachable": true,
  "packets_sent": 4,
  "packets_received": 4,
  "packet_loss": 0.0,
  "min_latency": 12.345,
  "avg_latency": 15.678,
  "max_latency": 20.123,
  "stddev_latency": 3.456,
  "response_times": [12.345, 15.678, 18.901, 20.123],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Partial Success Response

```json
{
  "status": "success",
  "host": "example.com",
  "reachable": true,
  "packets_sent": 4,
  "packets_received": 3,
  "packet_loss": 25.0,
  "min_latency": 45.678,
  "avg_latency": 50.123,
  "max_latency": 55.678,
  "stddev_latency": 5.432,
  "response_times": [45.678, 55.678, null, 49.012],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Failure Response

```json
{
  "status": "error",
  "host": "unreachable-host.com",
  "reachable": false,
  "packets_sent": 3,
  "packets_received": 0,
  "packet_loss": 100.0,
  "error": "Destination host unreachable",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Troubleshooting

### Common Errors

- **`Destination host unreachable`**: No route to the target host
  - Check network configuration and routing
  - Verify the host is on the same network or accessible via gateway
  - Check for network outages or misconfigurations

- **`Request timeout`**: No response received within timeout period
  - The host may be down or blocking ICMP
  - Increase timeout value for high-latency networks
  - Check firewall rules on target host

- **`Permission denied`**: Insufficient privileges to send ICMP packets
  - Run with appropriate user privileges (often requires root/admin)
  - Use sudo or run as administrator
  - Configure system to allow non-privileged ICMP

- **`Name or service not known`**: Unable to resolve hostname
  - Verify the hostname is correct and DNS is working
  - Check DNS configuration and network settings
  - Use IP address instead of hostname for testing

- **`Network unreachable`**: Local network configuration issue
  - Check local network interface status
  - Verify IP configuration and default gateway
  - Restart network services if needed

- **`Operation not permitted`**: ICMP operations blocked by system policy
  - Check system firewall settings
  - Verify ICMP is allowed in security policies
  - Run with elevated privileges if required

### Best Practices

1. Use appropriate packet sizes for different network types
2. Set reasonable timeouts based on expected network latency
3. Use multiple attempts to account for transient network issues
4. Monitor packet loss percentages for network quality assessment
5. Establish baseline latency for critical network paths
6. Test from multiple network locations if possible
7. Document expected response times for important hosts

### Performance Metrics

- **Latency**: Round-trip time for ICMP packets (lower is better)
- **Packet Loss**: Percentage of packets not returned (should be 0% for stable networks)
- **Jitter**: Variation in latency times (standard deviation)
- **Reachability**: Ability to establish ICMP communication with target

### Security Considerations

- Many networks block ICMP for security reasons
- Respect network policies and obtain proper authorization
- Avoid excessive pinging that could be perceived as scanning
- Be aware that some hosts intentionally don't respond to ICMP
- Use alternative connectivity checks (TCP) when ICMP is blocked
- Log ping attempts for audit purposes

### Use Cases

- **Network monitoring**: Continuous availability monitoring
- **Troubleshooting**: Isolate network connectivity issues
- **Performance testing**: Measure network latency and quality
- **Geographic testing**: Test connectivity from different locations
- **Service dependency checks**: Verify network prerequisites
- **Baseline establishment**: Create performance benchmarks
