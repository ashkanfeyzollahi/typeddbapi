"""
Synchronous connection pooling and connection management.
"""

import threading
from datetime import datetime, timedelta
from types import TracebackType
from typing import List, Optional, Union

from typeddbapi._types import Connection
from typeddbapi.exceptions import PoolError
from typeddbapi.utils import (
    build_connection_kwargs,
    import_driver_module,
    parse_conn_url,
)


def connect(url: str) -> Connection:
    """
    Create a connection to DB-API 2.0 compatible databases by URL.

    :param url: Database connection configuration URL.
    :type url: str
    :return: Return a database connection object.
    :rtype: Connection
    """

    config = parse_conn_url(url)
    assert "driver" in config

    driver = import_driver_module(config["driver"])
    kwargs = build_connection_kwargs(config)

    return driver.connect(**kwargs)


class ConnectionFactory:
    """
    Database connection factory for creating connections with URL that is passed to
    instance once when initializing.
    """

    def __init__(self, url: str) -> None:
        """
        Initialize ConnectionFactory instance.

        :param url: Database connection configuration URL.
        :type url: str
        """

        self._url = url

    def connect(self) -> Connection:
        """
        Create a connection to database.

        :return: Database driver connection object.
        :rtype: Connection
        """

        return connect(self._url)


class Pool:
    """Thread-safe connection pool for DB-API 2.0 compatible databases."""

    def __init__(
        self,
        url_or_factory: Union[str, ConnectionFactory],
        min_size: int = 1,
        max_size: int = 10,
        timeout: float = 30.0,
        max_queries: Optional[int] = None,
        max_inactive_seconds: Optional[float] = None,
        validation_query: Optional[str] = None,
    ) -> None:
        """
        Initialize Pool instance.

        :param url_or_factory: Database URL or connection factory.
        :type url_or_factory: Union[str, ConnectionFactory]
        :param min_size: Minimum connections to keep.
        :type min_size: int
        :param max_size: Maximum connections allowed.
        :type max_size: int
        :param timeout: Seconds to wait for connection.
        :type timeout: float
        :param max_queries: Recycle after this many queries.
        :type max_queries: Optional[int]
        :param max_inactive_seconds: Recycle after idle time.
        :type max_inactive_seconds: Optional[float]
        :param validation_query: SQL to test connection health.
        :type validation_query: Optional[str]
        """

        if not isinstance(url_or_factory, ConnectionFactory):
            url_or_factory = ConnectionFactory(url_or_factory)

        self._conn_factory = url_or_factory

        if min_size < 1 or max_size < 1:
            raise ValueError("Argument 'min_size'/'max_size' must not be lesser than 1")

        self._min_size = min_size
        self._max_size = max_size
        self._timeout = timeout
        self._max_queries = max_queries
        self._max_inactive_seconds = max_inactive_seconds
        self._validation_query = validation_query
        self._available: List[Connection] = []
        self._condition = threading.Condition()
        self._closed = False
        self._last_activity_time = datetime.now()

        with self._condition:
            self._maybe_grow()

    def _create_connections(self, count: int = 1) -> None:
        """
        (Not thread-safe) Create connections and make them available.

        :param count: Count of connections to create.
        :type count: int
        """

        while len(self._available) < self._max_size and count > 0:
            self._available.append(self._conn_factory.connect())
            count -= 1

    def _maybe_grow(self) -> None:
        """
        (Not thread-safe) Check if there is need to create connections, if so, create connections and store
        them.
        """

        if self._min_size - len(self._available) < 1:
            return

        self._create_connections(self._min_size - len(self._available))

    def _maybe_shrink(self) -> None:
        """
        (Not thread-safe) Check if there are more than maximum amount of connections or pool was inactive
        and remove them.
        """

        while len(self._available) > self._max_size:
            self._available.pop().close()

        if (
            datetime.now() - self._last_activity_time
            > timedelta(seconds=self._max_inactive_seconds or 30.0)
            and len(self._available) > self._min_size
        ):
            self._available.pop().close()

        self._last_activity_time = datetime.now()

    def _validate_connection(self, connection: Connection) -> bool:
        """
        Check if connection is still alive.

        :param connection: Connection to validate.
        :type connection: Connection
        :return: True if connection is still alive else False.
        :rtype: bool
        """

        try:
            cur = connection.cursor()
            cur.execute(self._validation_query or "SELECT 1")
            cur.close()
            return True
        except Exception:
            return False

    def acquire(self, timeout: Optional[float] = None) -> Connection:
        """
        (Thread-safe) Get a connection from the pool (blocks if none available).

        :param timeout:
        :type timeout: Optional[float]
        :return: A connection from the pool.
        :rtype: Connection
        """

        with self._condition:
            self._maybe_shrink()

            if not self._available:
                self._condition.wait(timeout or self._timeout)

                if self._closed:
                    raise PoolError("Pool is closed")

                if not self._available:
                    self._maybe_grow()

            conn = self._available.pop()
            self._maybe_grow()

            if self._validate_connection(conn):
                return conn

            return self.acquire(timeout)

    def close(self) -> None:
        """
        (Thread-safe) Close the pool and all connections.
        """

        with self._condition:
            self._closed = True

            for conn in self._available:
                conn.close()

            self._available.clear()

            self._condition.notify_all()

    def connection(self) -> PoolConnectionContextManager:
        """
        Return a PoolConnectionContextManager that acquires a connection and releases it
        automatically.
        """

        return PoolConnectionContextManager(self)

    def release(self, connection: Connection) -> None:
        """
        (Thread-safe) Return a connection to the pool.

        :param connection: Connection to release.
        :type connection: Connection
        """

        with self._condition:
            try:
                connection.rollback()
            except Exception:
                if self._validate_connection(connection):
                    self._maybe_grow()
                    return

            self._available.append(connection)
            self._condition.notify()
            self._maybe_shrink()

    def resize(
        self, min_size: Optional[int] = None, max_size: Optional[int] = None
    ) -> None:
        """
        (Thread-safe) Dynamically adjust pool size.

        :param min_size: Minimum amount of connections there must be.
        :type min_size: Optional[int]
        :param max_size: Maximum amount of connections there must be.
        :type max_size: Optional[int]
        """

        with self._condition:
            if min_size is not None:
                if min_size < 1:
                    raise ValueError("Argument 'min_size' must not be lesser than 1")
                self._min_size = min_size

            if max_size is not None:
                if max_size < 1:
                    raise ValueError("Argument 'max_size' must not be lesser than 1")
                self._max_size = max_size

            self._maybe_shrink()
            self._maybe_grow()


class PoolConnectionContextManager:
    """
    Pool connection context manager for acquiring connections and releasing them
    automatically.
    """

    def __enter__(self) -> Connection:
        """
        Acquire a connection from pool and return it.
        """

        self._conn = self._pool.acquire()
        return self._conn

    def __exit__(self, exc_type: type[Exception], exc: Exception, tb: TracebackType):
        """
        Release the connection that is acquired from pool.
        """

        if self._conn is not None:
            self._pool.release(self._conn)

    def __init__(self, pool: Pool) -> None:
        """
        Initialize PoolConnectionContextManager instance.

        :param pool: The pool that connection is acquired from.
        :type pool: Pool
        """

        self._pool = pool
        self._conn: Optional[Connection] = None
