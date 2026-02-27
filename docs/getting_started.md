---
icon: lucide/braces
---

# Getting Started!

In this we're going learn what you can do with `typeddbapi` and talk about what it supports.

## Establishing database connections

Establishing database connections with `typeddbapi` is easy, you pass your database URL and boom! you're connected!

```py
from typeddbapi import connect

with connect("sqlite:///database.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
    user = cursor.fetchone()
    print(user)
```

## Using ConnectionFactory to establish connections

Another way to create database connections is using `typeddbapi.ConnectionFactory`, which is a class that you pass database URL once and create connections multiple times:

```py
from typeddbapi import ConnectionFactory

conn_factory = ConnectionFactory("mysql://root:root@localhost/mydb")

with conn_factory.connect() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = %s", ("ashkan",))
    user = cursor.fetchone()
    print(user)
```

## Connection Pooling

Connection pooling is an extra from `typeddbapi` that prepares connections before usage so we don't allocate resources on every request, and when it get connections back, it resets their states and keeps them awake till it hits timeout so there are more connections prepared for reuse and blah blah blah...

`typeddbapi` provides these methods on `typeddbapi.Pool` instances:

* `.acquire()`: Get a connection from the pool (blocks if none available).

    ```py
    from typeddbapi import Pool

    pool = Pool("postgresql://user:pass@localhost/mydb")
    conn = pool.acquire()  # Blocks until connection available

    try:
        # Use the connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
    finally:
        # Always release connections back to the pool
        pool.release(conn)

    pool.close()
    ```

* `.close()`: Close the pool and all connections.

    ```py
    from typeddbapi import Pool

    pool = Pool("postgresql://user:pass@localhost/mydb")

    # Use the pool
    with pool.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        cursor.close()

    # Shut down the pool when application exits
    pool.close()  # All connections are properly closed
    ```

* `.connection()`: Context manager that auto-acquires and auto-releases.

    ```py
    from typeddbapi import Pool

    pool = Pool("postgresql://user:pass@localhost/mydb")

    # Connection is automatically acquired and released
    with pool.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
        cursor.close()
        conn.commit()  # Don't forget to commit!

    # No need to call release() - context manager handles it
    pool.close()
    ```

* `.release(connection)`: Return a connection to the pool.

    ```py
    from typeddbapi import Pool

    pool = Pool("postgresql://user:pass@localhost/mydb")
    conn = pool.acquire()

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET active = true WHERE id = %s", (1,))
        cursor.close()
        conn.commit()
    finally:
        # Always release - even if an error occurred
        pool.release(conn)  # Connection returns to pool for reuse

    pool.close()
    ```

* `.resize(min_size, max_size)`: Dynamically adjust pool size.

    ```py
    from typeddbapi import Pool

    pool = Pool("postgresql://user:pass@localhost/mydb", min_size=2, max_size=5)

    # During peak load, increase pool capacity
    pool.resize(min_size=4, max_size=10)  # Pool adapts to demand

    with pool.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM active_sessions")
        count = cursor.fetchone()[0]
        cursor.close()

    # Later, scale back down
    pool.resize(min_size=2, max_size=5)

    pool.close()
    ```

## Asynchronous Support

To use asynchronous version, you need to import `async_connect`, `AsyncConnectionFactory` and `AsyncPool` from `typeddbapi.async_`. Anything else is exactly like synchronous version just usage of `await` and `async` rather than synchronous keywords.
