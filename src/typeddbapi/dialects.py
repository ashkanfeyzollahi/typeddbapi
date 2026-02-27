"""
typeddbapi dialect registry
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class DialectType(Enum):
    """Classification of database dialects by connection method."""

    FILESYSTEM_BASED = 0
    NETWORK_BASED = 1


@dataclass
class Param:
    """Definition of a connection parameter for a database dialect."""

    name: str
    type: type


@dataclass
class Dialect:
    """Definition of a database dialect and its connection parameters."""

    name: str
    default_driver: str
    required_params: List[Param]
    optional_params: List[Param]
    dialect_type: DialectType = DialectType.NETWORK_BASED
    default_port: Optional[int] = None


dialects_dict: Dict[str, Dialect] = {
    "sqlite": Dialect(
        "sqlite",
        "sqlite3",
        [Param("database", str)],
        [
            Param("timeout", float),
            Param("detect_types", int),
            Param("isolation_level", str),
            Param("check_same_thread", bool),
            Param("cached_statements", int),
            Param("uri", bool),
        ],
        DialectType.FILESYSTEM_BASED,
    ),
    "postgresql": Dialect(
        "postgresql",
        "psycopg2",
        [Param("database", str)],
        [
            Param("host", str),
            Param("port", int),
            Param("user", str),
            Param("password", str),
            Param("sslmode", str),
            Param("connect_timeout", int),
            Param("keepalives_idle", int),
            Param("application_name", str),
        ],
    ),
    "mysql": Dialect(
        "mysql",
        "mysql",
        [Param("database", str)],
        [
            Param("host", str),
            Param("port", int),
            Param("user", str),
            Param("password", str),
            Param("charset", str),
            Param("unix_socket", str),
            Param("ssl_ca", str),
            Param("ssl_cert", str),
            Param("ssl_key", str),
        ],
    ),
    "oracle": Dialect(
        "oracle",
        "cx_oracle",
        [Param("database", str)],
        [
            Param("host", str),
            Param("port", int),
            Param("user", str),
            Param("password", str),
            Param("mode", str),
            Param("threaded", bool),
            Param("events", bool),
            Param("purity", str),
        ],
    ),
    "mssql": Dialect(
        "mssql",
        "pyodbc",
        [Param("database", str)],
        [
            Param("host", str),
            Param("port", int),
            Param("user", str),
            Param("password", str),
            Param("driver", str),
            Param("trusted_connection", bool),
            Param("encrypt", bool),
            Param("timeout", int),
        ],
    ),
}
