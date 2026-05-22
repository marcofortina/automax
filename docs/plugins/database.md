# Database plugins

Database plugins run on the controller and connect to the selected database using
DB-API compatible drivers. SQLite is built into Python. PostgreSQL, MySQL and
Oracle drivers are optional extras.

```bash
pip install 'automax[postgres]'
pip install 'automax[mysql]'
pip install 'automax[oracle]'
pip install 'automax[database]'
```

All database plugins support DDL, DML and SELECT statements. They open a
transaction, commit on success by default and roll back on failure. Autocommit is
not enabled.

Common parameters:

```yaml
connection: {}
query: "SELECT ..."          # one statement
statements: []               # or multiple statements
query_params: []             # DB driver parameters for the final statement
output: rows                 # rows, scalar, json, none
fetch: all                   # all, one, none
commit: true                 # false rolls back at the end intentionally
```

Secrets are resolved through the normal env/file secret providers before
rendering:

```yaml
password: "{{ secrets.db_password }}"
```

## `db.sqlite.query`

```yaml
- id: create_table
  use: db.sqlite.query
  with:
    connection:
      path: /tmp/app.sqlite
    statements:
      - "CREATE TABLE IF NOT EXISTS app_config (key TEXT PRIMARY KEY, value TEXT)"
      - "INSERT OR REPLACE INTO app_config(key, value) VALUES ('version', '1.0.0')"
    output: none

- id: read_version
  use: db.sqlite.query
  with:
    connection:
      path: /tmp/app.sqlite
    query: "SELECT value FROM app_config WHERE key = ?"
    query_params: [version]
    output: scalar
    fetch: one
  register:
    database_version: data.scalar
```

## `db.postgres.query`

Requires `automax[postgres]`.

```yaml
- id: postgres_query
  use: db.postgres.query
  with:
    connection:
      host: db01.example.com
      port: 5432
      database: appdb
      user: app
      password: "{{ secrets.postgres_password }}"
    query: "SELECT current_database() AS database_name"
    output: json
```

A DSN can also be used:

```yaml
connection:
  dsn: "postgresql://app:{{ secrets.postgres_password }}@db01/appdb"
```

## `db.mysql.query`

Requires `automax[mysql]`.

```yaml
- id: mysql_query
  use: db.mysql.query
  with:
    connection:
      host: db01.example.com
      port: 3306
      database: appdb
      user: app
      password: "{{ secrets.mysql_password }}"
    query: "SELECT VERSION() AS version"
    output: rows
```

## `db.oracle.query`

Requires `automax[oracle]`.

```yaml
- id: oracle_query
  use: db.oracle.query
  with:
    connection:
      dsn: db01.example.com/FREEPDB1
      user: app
      password: "{{ secrets.oracle_password }}"
    query: "SELECT sysdate FROM dual"
    output: rows
```

## Scaling to new databases

Add a new module under `automax.plugins.db`, subclass `DatabaseQueryPlugin`, and
register the canonical plugin in `build_builtin_registry()` or load it through an
external plugin path. The shared base already handles statement validation,
output shaping and common result metadata.
