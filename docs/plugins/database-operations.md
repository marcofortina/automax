# Database Operations Plugin

Execute database operations on various database systems.

## Description

This plugin enables executing SQL queries and commands on different database systems including PostgreSQL, MySQL, SQLite, and Oracle. It supports parameterized queries, transactions, and returns results in structured format.

## Configuration

### Required Parameters

- `connection_string` (string): Database connection string
- `query` (string): SQL query to execute
- `action` (string): Operation type - `execute`, `fetchone`, `fetchall`

### Optional Parameters

- `parameters` (object|array): Query parameters for parameterized queries
- `commit` (boolean): Whether to commit the transaction (default: true for execute actions)
- `timeout` (integer): Query timeout in seconds

## Examples

### Execute INSERT Query (PostgreSQL)

```yaml
- name: insert_user
  plugin: database_operations
  parameters:
    connection_string: "postgresql://user:password@localhost:5432/mydb"
    query: "INSERT INTO users (name, email) VALUES (%s, %s)"
    action: "execute"
    parameters:
      - "John Doe"
      - "john@example.com"
    commit: true
```

### Execute SELECT Query with Fetch All (MySQL)

```yaml
- name: get_all_users
  plugin: database_operations
  parameters:
    connection_string: "mysql://user:password@localhost:3306/mydb"
    query: "SELECT * FROM users WHERE active = %s"
    action: "fetchall"
    parameters:
      - true
```

### Execute SELECT Query with Fetch One (SQLite)

```yaml
- name: get_user_count
  plugin: database_operations
  parameters:
    connection_string: "sqlite:///path/to/database.db"
    query: "SELECT COUNT(*) as user_count FROM users"
    action: "fetchone"
```

### Execute UPDATE Query with Parameters

```yaml
- name: update_user_email
  plugin: database_operations
  parameters:
    connection_string: "postgresql://user:password@localhost:5432/mydb"
    query: "UPDATE users SET email = %s WHERE id = %s"
    action: "execute"
    parameters:
      - "newemail@example.com"
      - 123
    commit: true
```

### Execute Transaction with Multiple Queries

```yaml
- name: transfer_funds
  plugin: database_operations
  parameters:
    connection_string: "mysql://user:password@localhost:3306/bank"
    query: |
      UPDATE accounts SET balance = balance - %s WHERE id = %s;
      UPDATE accounts SET balance = balance + %s WHERE id = %s;
    action: "execute"
    parameters:
      - 100.00
      - 1
      - 100.00
      - 2
    commit: true
```

## Return Values

### Execute Action (INSERT/UPDATE/DELETE)

```json
{
  "status": "success",
  "action": "execute",
  "query": "INSERT INTO users (name, email) VALUES (%s, %s)",
  "row_count": 1,
  "message": "Query executed successfully"
}
```

### FetchOne Action

```json
{
  "status": "success",
  "action": "fetchone",
  "query": "SELECT * FROM users WHERE id = %s",
  "result": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2023-01-01 00:00:00"
  }
}
```

### FetchAll Action

```json
{
  "status": "success",
  "action": "fetchall",
  "query": "SELECT * FROM users WHERE active = %s",
  "results": [
    {
      "id": 123,
      "name": "John Doe",
      "email": "john@example.com"
    },
    {
      "id": 124,
      "name": "Jane Smith",
      "email": "jane@example.com"
    }
  ],
  "row_count": 2
}
```

## Troubleshooting

### Common Errors

- **`Connection failed`**: Unable to connect to database
  - Verify connection string format and credentials
  - Check if database server is running and accessible
  - Ensure network connectivity and firewall rules

- **`Authentication failed`**: Invalid username or password
  - Verify database credentials
  - Check if user has necessary permissions
  - Ensure user is not locked or expired

- **`Syntax error in query`**: Invalid SQL syntax
  - Validate SQL query syntax
  - Check for missing semicolons or typos
  - Verify table and column names exist

- **`Table does not exist`**: Referenced table not found
  - Verify database schema and table names
  - Check if using correct database
  - Ensure migrations have been applied

- **`Timeout`**: Query execution timed out
  - Increase timeout parameter for long-running queries
  - Check database performance and indexes
  - Optimize query for better performance

- **`Transaction conflict`**: Transaction-related issues
  - Ensure proper transaction handling
  - Check for deadlocks or lock timeouts
  - Use appropriate isolation levels

### Connection String Formats

- **PostgreSQL**: `postgresql://username:password@host:port/database`
- **MySQL**: `mysql://username:password@host:port/database`
- **SQLite**: `sqlite:///path/to/database.db`
- **Oracle**: `oracle://username:password@host:port/database`

### Best Practices

1. Always use parameterized queries to prevent SQL injection
2. Handle database connections properly and close them after use
3. Use transactions for multiple related operations
4. Implement proper error handling and logging
5. Use connection pooling for frequent database operations
6. Validate and sanitize all user inputs
7. Use appropriate indexes for better query performance

### Security Considerations

- Never embed database credentials in code
- Use environment variables or secret managers for connection strings
- Implement least privilege principle for database users
- Regularly rotate database passwords
- Encrypt sensitive data in database
- Audit database access and queries
