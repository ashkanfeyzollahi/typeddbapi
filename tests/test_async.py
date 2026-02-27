"""
Test asynchronous connection pooling and connection management.
"""

import pytest

from typeddbapi.async_ import AsyncConnectionFactory

DATABASE_URL = "sqlite+aiosqlite:///database.db"
conn_factory = AsyncConnectionFactory(DATABASE_URL)


@pytest.mark.asyncio
async def test_conn_factory() -> None:
    """
    Test class 'AsyncConnectionFactory'
    """

    db_conn = await conn_factory.connect()

    cursor = await db_conn.cursor()
    await cursor.execute("SELECT 1")
    await cursor.close()
    await db_conn.close()


# TODO: Write tests for AsyncPool
