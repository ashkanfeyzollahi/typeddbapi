---
icon: lucide/book-open
---

# typeddbapi

A lightweight, type-hinted wrapper around Python's DB-API 2.0.

## What is typeddbapi?

**typeddbapi** provides a simple way to connect to databases using URL strings, with full type hints and optional connection pooling. You write raw SQL for your specific database—typeddbapi just passes it through to your driver.

## Why typeddbapi?

- **Raw SQL First** - No ORM magic, no query translation. You write the SQL you want to execute.
- **Type-Hinted Throughout** - Full type annotations for better IDE support and runtime type checking.
- **Driver Agnostic** - Works with any DB-API 2.0 compatible driver (psycopg, sqlite3, mysql-connector, asyncpg, aiosqlite, and more).
- **Optional Pooling** - Connection pool utilities available when you need them.
- **Async Support** - Both synchronous and asynchronous APIs with the same intuitive interface.
!!! WARNING "Async support is only for asynchronous drivers (e.g. aiosqlite)"

## What typeddbapi is NOT

- Not a cross-database compatibility layer
- Not an ORM
- Not a query builder
- Not a SQL validator or translator

## typeddbapi Philosophy

typeddbapi directly gives your raw SQL query to the database driver specified in the URL rather than trying to abstract it away. If someone wants an ORM, they can build one on top.

## Connection URLs

typeddbapi uses standard RFC-1738 URLs with dialect and optional driver:

```plain
dialect[+driver]://user:pass@host:port/database
```

Examples:
- `postgresql://localhost/mydb`
- `postgresql+asyncpg://localhost/mydb`
- `mysql+pymysql://localhost/mydb`
- `sqlite:///path/to/file.db`

The dialect tells typeddbapi what database you're using, and the optional driver specifies which DB-API 2.0 driver to use. If no driver is specified, the dialect's default driver is used.

## Quick Peek

```python
from typeddbapi import connect, ConnectionFactory, Pool

DATABASE_URL = "postgresql+psycopg2://user:pass@localhost/mydb"

# Simple connection
with connect(DATABASE_URL) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
    user = cursor.fetchone()
    print(user)
```

For more details, look at [documentation](https://ashkanfeyzollahi.github.io/typeddbapi).

## Requirements

- Python 3.7+
- A DB-API 2.0 compliant driver for your database (install separately)

## License

MIT
