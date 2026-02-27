"""
Utility functions for typeddbapi internal use.
"""

import importlib
from types import ModuleType
from typing import Any, Dict, TypeVar, Union
from urllib.parse import parse_qs, urlparse

from typeddbapi._types import ConnectionConfig
from typeddbapi.dialects import dialects_dict, DialectType, Param
from typeddbapi.exceptions import ConfigurationError, InterfaceError


T = TypeVar("T")


def _convert_type(value: str, expected_type: type) -> Union[str, int, float, bool]:
    """
    Convert string instance to expected type.

    This function doesn't work for types other than str, int, float and bool, because
    there is no need for. Used in connection configuration URL parsing to convert query
    parameters into their expected type.

    :param value: String instance to convert its type.
    :type value: str
    :param expected_type: Type to convert string instance to.
    :type expected_type: type
    :return: String instance converted into expected type.
    :rtype: Union[str, int, float, bool]
    :raises ConfigurationError: Raised when string instance is invalid for converting \
        into expected type.
    """

    if expected_type in (int, float):
        try:
            return expected_type(value)
        except ValueError:
            raise ConfigurationError(
                f"Cannot convert {value!r} to {expected_type.__name__}"
            )

    elif expected_type is bool:
        value_lower = value.lower()
        if value_lower in ("true", "yes", "1"):
            return True
        elif value_lower in ("false", "no", "0"):
            return False
        else:
            raise ConfigurationError(f"Boolean value expected, got {value!r}")

    return value


def build_connection_kwargs(config: ConnectionConfig) -> Dict[str, Any]:
    """
    Remove typeddbapi internal parameters from config and pop extras and merge it with
    config.

    :param config: Database connection configuration.
    :type config: ConnectionConfig
    :return: Prepared keyword arguments ready to pass directly to connection function.
    :rtype: Dict[str, Any]
    """

    assert "extras" in config

    extras = config.pop("extras")
    config.pop("driver")
    config.pop("dialect")

    merged_config = {}
    merged_config.update(extras)
    merged_config.update(config)

    return merged_config


def import_driver_module(driver: str) -> ModuleType:
    """
    Import database driver module and validate it.

    This function is used to import driver module safely and with validation.

    :raises ConfigurationError: Raised when cannot import driver module.
    :raises InterfaceError: Raised when driver module violates DB-API 2.0 rules.
    :return: Database driver module.
    :rtype: ModuleType
    """

    try:
        driver_module = importlib.import_module(driver)

    except ImportError:
        raise ConfigurationError(
            f"Couldn't import driver {driver!r}! Make "
            "sure your driver is installed and importable."
        )

    if not hasattr(driver_module, "connect"):
        raise InterfaceError(
            f"Driver {driver!r} violates DB-API 2.0 rules by not having "
            "`connect` function. Make sure you're using a DB-API 2.0 compatible driver."
        )

    return driver_module


def parse_conn_url(url: str) -> ConnectionConfig:
    """
    Parse database URL into driver name and connection parameters.

    This function is used to parse connection configuration URL and then convert
    parameters into a TypedDict, and then pass parameters to database driver's connect
    function as keyword arguments to connect.

    :param url: Connection URL to parse.
    :type url: str
    :return: Parsed connection configuration URL.
    :rtype: ConnectionConfig
    :raises ConfigurationError: Raised when URL scheme is empty, any of required \
        parameters are missing in URL, or an invalid parameter is passed via URL.
    """

    parse_result = urlparse(url)

    config: dict[str, Any] = {"dialect": None, "driver": None}

    extras: dict[str, Any] = parse_qs(parse_result.query)
    extras = {key: extras[key][0] for key in extras}
    config["extras"] = extras

    scheme = parse_result.scheme
    if not scheme:
        raise ConfigurationError("URL must have a scheme (dialect[+driver]://)")

    if "+" in scheme:
        dialect_name, driver = scheme.split("+")
        config["dialect"] = dialect_name
        config["driver"] = driver

    else:
        config["dialect"] = scheme

    dialect = dialects_dict[config["dialect"]]

    if config["driver"] is None:
        config["driver"] = dialect.default_driver

    port = dialect.default_port

    if parse_result.port is not None:
        port = parse_result.port

    config["port"] = port

    host = parse_result.hostname

    if host is None and dialect.dialect_type == DialectType.NETWORK_BASED:
        host = "127.0.0.1"

    config["host"] = host

    config["user"] = parse_result.username
    config["password"] = parse_result.password

    database = parse_result.path

    if database.startswith("/"):
        database = database[1:]

    if not database:
        database = None

    config["database"] = database
    config["autocommit"] = extras.pop("autocommit", None)

    config = {key: config[key] for key in config if config[key] is not None}

    all_params = (
        dialect.optional_params + dialect.required_params + [Param("autocommit", bool)]
    )

    for param in all_params:
        if param.name in config:
            config[param.name] = _convert_type(config[param.name], param.type)

        elif param.name in extras:
            extras[param.name] = _convert_type(extras[param.name], param.type)

    for param in dialect.required_params:
        if param.name not in config and param.name not in extras:
            raise ConfigurationError(
                f"Parameter {param.name!r} is required but is not given"
            )

    all_param_names = [param.name for param in all_params]
    INTERNAL_PARAMS = ["dialect", "driver", "extras", "autocommit"]
    valid_keys = all_param_names + INTERNAL_PARAMS

    for key in list(config.keys()) + list(extras.keys()):
        if key not in valid_keys:
            raise ConfigurationError(
                f"Got an unexpected parameter {key!r} (Must have been one of {valid_keys})"
            )

    return ConnectionConfig(**config)
