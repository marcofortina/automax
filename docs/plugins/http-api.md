# HTTP/API plugins

HTTP plugins run from the controller. They are useful for health checks, API
calls and deployment gates.

## `http.request`

Runs an HTTP request and returns status, body and headers.

```yaml
- id: call_api
  use: http.request
  with:
    method: POST
    url: "https://api.example.com/deploy"
    headers:
      Authorization: "Bearer {{ secrets.api_token }}"
      Content-Type: application/json
    json:
      version: "{{ vars.version }}"
    timeout: 30
  register:
    api_status: data.status
```

## `http.assert`

Fails immediately unless the HTTP response matches the expected condition.

```yaml
- id: assert_health
  use: http.assert
  with:
    url: "http://{{ server.host }}:8080/health"
    status: 200
    contains: ok
    timeout: 10
```

## `http.wait`

Polls until the HTTP endpoint matches or timeout expires.

```yaml
- id: wait_health
  use: http.wait
  with:
    url: "http://{{ server.host }}:8080/health"
    status: 200
    contains: ok
    timeout: 120
    interval: 5
```
