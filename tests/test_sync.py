"""
Test synchronous connection pooling and connection management.
"""

from typeddbapi import ConnectionFactory

DATABASE_URL = "sqlite:///database.db"
conn_factory = ConnectionFactory(DATABASE_URL)


def test_conn_factory() -> None:
    """
    Test class 'ConnectionFactory'
    """

    db_conn = conn_factory.connect()

    cursor = db_conn.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
    db_conn.close()


# TODO: Write tests for Pool
