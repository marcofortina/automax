# Database Operations Plugin

Perform database operations.

## Configuration

**Required:**
- `database_type`: Database type (sqlite)
- `query`: SQL query to execute

**Optional:**
- `host`: Database host
- `port`: Database port
- `username`: Database username
- `password`: Database password
- `database`: Database name/path
- `parameters`: Query parameters

## Example

```yaml
plugin: database_operations
config:
  database_type: "sqlite"
  database: ":memory:"
  query: "SELECT * FROM users WHERE age > ?"
  parameters: [18]
```
