"""
Custom exceptions hierarchy
"""


class TypedDBAPIError(Exception):
    """Base exception for all typeddbapi errors"""

    pass


class PoolError(TypedDBAPIError):
    """Raised when pool operations fail"""

    pass


class ConfigurationError(TypedDBAPIError):
    """Raised when configuration is invalid"""

    pass


class InterfaceError(TypedDBAPIError):
    """Raised for DB-API interface violations"""

    pass
