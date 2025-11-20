# Run HTTP Request Plugin

Execute HTTP requests to interact with web services and APIs.

## Description

This plugin enables making HTTP requests to various endpoints. It supports multiple HTTP methods (GET, POST, PUT, DELETE, etc.), headers, query parameters, and request body with automatic JSON handling.

## Configuration

### Required Parameters

- `url` (string): The URL to send the request to
- `method` (string): HTTP method - `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS`

### Optional Parameters

- `headers` (object): HTTP headers as key-value pairs
- `query_params` (object): Query parameters as key-value pairs
- `body` (string|object): Request body (string for raw, object for JSON)
- `timeout` (integer): Request timeout in seconds (default: 30)
- `verify_ssl` (boolean): Verify SSL certificates (default: true)
- `auth` (object): Authentication credentials with `username` and `password` fields
- `follow_redirects` (boolean): Follow HTTP redirects (default: true)

## Examples

### Simple GET Request

```yaml
- name: get_user_data
  plugin: run_http_request
  parameters:
    url: "https://api.example.com/users/123"
    method: "GET"
    headers:
      Accept: "application/json"
      User-Agent: "Automax/1.0"
```

### POST Request with JSON Body

```yaml
- name: create_new_user
  plugin: run_http_request
  parameters:
    url: "https://api.example.com/users"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer ${api_token}"
    body:
      name: "John Doe"
      email: "john@example.com"
      role: "user"
```

### POST Request with Raw Body

```yaml
- name: send_xml_data
  plugin: run_http_request
  parameters:
    url: "https://api.example.com/data"
    method: "POST"
    headers:
      Content-Type: "application/xml"
    body: "<?xml version='1.0'?><user><name>John</name></user>"
```

### Request with Query Parameters and Authentication

```yaml
- name: search_products
  plugin: run_http_request
  parameters:
    url: "https://api.example.com/products"
    method: "GET"
    query_params:
      category: "electronics"
      min_price: "100"
      max_price: "500"
    auth:
      username: "api_user"
      password: "api_password"
    timeout: 60
```

### Request with SSL Verification Disabled

```yaml
- name: test_internal_endpoint
  plugin: run_http_request
  parameters:
    url: "https://internal-api.local/users"
    method: "GET"
    verify_ssl: false
    timeout: 10
```

## Return Values

### Success Response

```json
{
  "status": "success",
  "url": "https://api.example.com/users/123",
  "method": "GET",
  "status_code": 200,
  "headers": {
    "Content-Type": "application/json",
    "Content-Length": "125"
  },
  "body": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "response_time": 0.45,
  "cookies": {}
}
```

### Error Response

```json
{
  "status": "error",
  "url": "https://api.example.com/users/999",
  "method": "GET",
  "status_code": 404,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "error": "User not found",
    "code": 404
  },
  "response_time": 0.23,
  "error": "HTTP 404: Not Found"
}
```

## Troubleshooting

### Common Errors

- **`ConnectionError`**: Unable to connect to the server
  - Verify the URL is correct and accessible
  - Check network connectivity and DNS resolution
  - Ensure the server is running and accepting connections

- **`Timeout`**: Request timed out
  - Increase timeout value for slow endpoints
  - Check server performance and network latency
  - Verify the endpoint is responsive

- **`SSLError`**: SSL certificate verification failed
  - Verify the certificate is valid and trusted
  - Use `verify_ssl: false` for self-signed certificates (development only)
  - Check certificate expiration dates

- **`HTTPError`**: HTTP error status code (4xx, 5xx)
  - Check the API documentation for expected status codes
  - Verify request parameters, headers, and body format
  - Ensure authentication credentials are valid

- **`InvalidURL`**: Malformed or invalid URL
  - Verify URL format and protocol (http:// or https://)
  - Check for typos in the URL
  - Ensure special characters are properly encoded

- **`JSONDecodeError`**: Unable to parse response as JSON
  - Check if the response is actually JSON format
  - Verify the Content-Type header is application/json
  - Use raw body access for non-JSON responses

### Best Practices

1. Always handle sensitive data (tokens, passwords) securely
2. Use appropriate timeouts for different types of requests
3. Implement retry logic for transient failures
4. Validate response status codes and handle errors gracefully
5. Use headers appropriately (Content-Type, Accept, Authorization)
6. Monitor API rate limits and implement backoff strategies

### HTTP Methods Guide

- `GET`: Retrieve data from server (should not modify data)
- `POST`: Create new resources or submit data
- `PUT`: Update existing resources (full update)
- `PATCH`: Partial update of resources
- `DELETE`: Remove resources
- `HEAD`: Retrieve headers only
- `OPTIONS`: Get supported methods for endpoint

### Status Code Categories

- `2xx`: Success (200 OK, 201 Created, 204 No Content)
- `3xx`: Redirection (301 Moved, 304 Not Modified)
- `4xx`: Client errors (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found)
- `5xx`: Server errors (500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable)
