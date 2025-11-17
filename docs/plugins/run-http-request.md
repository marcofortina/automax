# HTTP Request Plugin

Make HTTP requests to APIs.

## Configuration

**Required:**
- `url`: Target URL

**Optional:**
- `method`: HTTP method (default: GET)
- `headers`: Request headers
- `data`: Request body data
- `params`: Query parameters
- `timeout`: Request timeout in seconds (default: 30)
- `verify_ssl`: Verify SSL certificates (default: true)
- `auth_username`: Username for Basic Authentication
- `auth_password`: Password for Basic Authentication

## Example

```yaml
plugin: run_http_request
config:
  url: "https://api.example.com/data"
  method: "POST"
  headers:
    Authorization: "Bearer token123"
  data: '{"key": "value"}'
  timeout: 30
```

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `url`: The target URL
- `method`: The HTTP method used
- `status_code`: The HTTP status code
- `headers`: The response headers
- `content`: The response content
- `elapsed`: The request elapsed time in seconds
