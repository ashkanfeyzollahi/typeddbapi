"""
Test utility functions those are for typeddbapi internal use.
"""

import pytest

from typeddbapi.exceptions import ConfigurationError, InterfaceError
from typeddbapi.utils import (
    build_connection_kwargs,
    import_driver_module,
    parse_conn_url,
)


TEST_DATABASE_URL = "sqlite:///database.db?timeout=5.0&autocommit=true"
TEST_INVALID1_DATABASE_URL = "sqlite+blahblahblah:///database.db"
TEST_INVALID2_DATABASE_URL = "sqlite+sys:///database.db"
TEST_INVALID3_DATABASE_URL = "sqlite:///database.db?invalid_option=huh"


def test_build_connection_kwargs() -> None:
    """
    Test utility function 'build_connection_kwargs'
    """

    conn_config = parse_conn_url(TEST_DATABASE_URL)
    conn_kwargs = build_connection_kwargs(conn_config)

    assert conn_kwargs["timeout"] == 5.0


def test_import_driver_module() -> None:
    """
    Test utility function 'build_connection_kwargs'
    """

    conn_config1 = parse_conn_url(TEST_DATABASE_URL)
    assert "driver" in conn_config1

    import_driver_module(conn_config1["driver"])

    with pytest.raises(ConfigurationError):
        conn_config2 = parse_conn_url(TEST_INVALID1_DATABASE_URL)
        assert "driver" in conn_config2

        import_driver_module(conn_config2["driver"])

    with pytest.raises(InterfaceError):
        conn_config3 = parse_conn_url(TEST_INVALID2_DATABASE_URL)
        assert "driver" in conn_config3

        import_driver_module(conn_config3["driver"])


def test_parse_conn_url() -> None:
    """
    Test utility function 'parse_conn_url'
    """

    with pytest.raises(ConfigurationError):
        parse_conn_url(TEST_INVALID3_DATABASE_URL)
