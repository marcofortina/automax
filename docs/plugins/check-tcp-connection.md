# Check TCP Connection Plugin

Test TCP connectivity to remote hosts and ports.

## Description

This plugin enables testing TCP connectivity to specified hosts and ports. It's useful for verifying network connectivity, checking service availability, and monitoring network endpoints.

## Configuration

### Required Parameters

- `host` (string): Target hostname or IP address
- `port` (integer): Target port number

### Optional Parameters

- `timeout` (integer): Connection timeout in seconds (default: 10)
- `source_port` (integer): Source port to use for connection (default: random)
- `attempts` (integer): Number of connection attempts (default: 1)
- `retry_delay` (integer): Delay between retries in seconds (default: 1)

## Examples

### Basic TCP Connection Test

```yaml
- name: check_web_server
  plugin: check_tcp_connection
  parameters:
    host: "example.com"
    port: 80
    timeout: 5
```

### Test Database Port

```yaml
- name: check_database
  plugin: check_tcp_connection
  parameters:
    host: "db-server.example.com"
    port: 5432
    timeout: 10
```

### Test with Multiple Attempts

```yaml
- name: check_flaky_service
  plugin: check_tcp_connection
  parameters:
    host: "api.service.com"
    port: 443
    attempts: 3
    retry_delay: 2
    timeout: 15
```

### Test with Specific Source Port

```yaml
- name: check_from_fixed_port
  plugin: check_tcp_connection
  parameters:
    host: "192.168.1.100"
    port: 22
    source_port: 54321
    timeout: 5
```

### Test Local Service

```yaml
- name: check_local_redis
  plugin: check_tcp_connection
  parameters:
    host: "localhost"
    port: 6379
    timeout: 3
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "host": "example.com",
  "port": 80,
  "connected": true,
  "response_time": 0.045,
  "attempts": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Failure Response

```json
{
  "status": "error",
  "host": "example.com",
  "port": 8080,
  "connected": false,
  "error": "Connection refused",
  "attempts": 3,
  "response_time": 10.123,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Troubleshooting

### Common Errors

- **`Connection refused`**: No service listening on the target port
  - Verify the service is running on the target host
  - Check if the correct port is being used
  - Ensure the service is bound to the correct interface

- **`Connection timeout`**: No response received within timeout period
  - Increase timeout value for slow connections
  - Check network connectivity and firewall rules
  - Verify the host is reachable via ICMP or other methods

- **`Host not found`**: Unable to resolve hostname
  - Verify the hostname is correct and DNS is working
  - Check DNS configuration and network settings
  - Use IP address instead of hostname for testing

- **`Network unreachable`**: No route to the target host
  - Check network configuration and routing tables
  - Verify the host is on the same network or accessible via gateway
  - Check for network outages or misconfigurations

- **`Permission denied`**: Insufficient privileges to create socket
  - Run with appropriate user privileges
  - Check SELinux/AppArmor policies
  - Verify user has network access permissions

- **`Port in use`**: Source port already in use (when using specific source_port)
  - Use a different source port
  - Let the system choose a random port (omit source_port parameter)

### Common Ports for Testing

- `22`: SSH
- `80`: HTTP
- `443`: HTTPS
- `53`: DNS
- `25`: SMTP
- `143`: IMAP
- `993`: IMAPS
- `110`: POP3
- `995`: POP3S
- `5432`: PostgreSQL
- `3306`: MySQL
- `27017`: MongoDB
- `6379`: Redis
- `9200`: Elasticsearch

### Best Practices

1. Use appropriate timeouts for different types of services
2. Implement retry logic for transient network failures
3. Monitor connection times for performance baseline
4. Test from multiple network locations if possible
5. Use both hostname and IP address testing
6. Document expected response times for critical services
7. Set up alerting for connection failures

### Monitoring Scenarios

- **Service health checks**: Verify critical services are accessible
- **Network troubleshooting**: Isolate network vs service issues
- **Firewall testing**: Verify port accessibility through firewalls
- **Load balancer health**: Check backend service availability
- **DNS validation**: Test hostname resolution and connectivity
- **Geographic monitoring**: Test from different network locations

### Security Considerations

- Be cautious when testing ports on external networks
- Respect network policies and obtain proper authorization
- Avoid excessive testing that could be perceived as scanning
- Use appropriate source ports to avoid firewall blocks
- Log connection attempts for audit purposes
- Implement rate limiting for automated testing
