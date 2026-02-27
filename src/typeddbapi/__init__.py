"""
A lightweight, type-hinted wrapper around Python's DB-API 2.0.
"""

from typeddbapi.sync import connect, Connection, ConnectionFactory, Pool


__all__ = ("connect", "Connection", "ConnectionFactory", "Pool")
