# Database Operations Plugin

Execute database operations using ODBC connection strings.

## Configuration

**Required:**
- `connection_string`: ODBC connection string
- `query`: SQL query to execute
- `action`: Operation type - "select", "insert", "update", "delete", "execute"

**Optional:**
- `parameters`: Query parameters as list

## Example

```yaml
plugin: database_operations
config:
  connection_string: "DRIVER={SQL Server};SERVER=localhost;DATABASE=test;UID=user;PWD=password"
  query: "SELECT * FROM users WHERE id = ?"
  action: "select"
  parameters: [1]
```

## Supported Actions

- **select**: Execute SELECT queries and return results
- **insert**: Execute INSERT queries, returns affected rows and lastrowid
- **update**: Execute UPDATE queries, returns affected rows
- **delete**: Execute DELETE queries, returns affected rows
- **execute**: Execute DDL or other statements, returns affected rows

## Return Values

The plugin returns a dictionary with:
- `status`: "success" or "failure"
- `row_count`: Number of affected/returned rows
- `columns`: List of column names (for SELECT)
- `rows`: List of result rows (for SELECT)
- `lastrowid`: Last inserted row ID (for INSERT)
