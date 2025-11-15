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

## Example

```yaml
plugin: run_http_request
config:
  url: "https://api.example.com/data"
  method: "POST"
  headers:
    Authorization: "Bearer token123"
  data: '{"key": "value"}'
```
