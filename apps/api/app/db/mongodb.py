"""
COGNARC — MongoDB Async Client (Motor)
apps/api/app/db/mongodb.py

T3.3: Motor async client singleton with connect_db() / close_db() lifecycle hooks.
§08: Use Motor async driver. NEVER use pymongo synchronously.
§06: Only repositories/ access the DB. This module provides the connection.
"""
from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logger import get_logger

_logger = get_logger("db.mongodb")

# Module-level client and database singletons
_client: Optional[AsyncIOMotorClient] = None  # type: ignore[type-arg]
_database: Optional[AsyncIOMotorDatabase] = None  # type: ignore[type-arg]


async def connect_db() -> None:
    """
    Open the Motor async connection to MongoDB Atlas.
    Called during FastAPI lifespan startup.
    Raises on connection failure — ensures hard fail at boot.
    """
    global _client, _database

    if not settings.MONGODB_URL:
        _logger.warning("MONGODB_URL not set — database features will be unavailable")
        return

    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        maxPoolSize=10,
        minPoolSize=1,
    )

    _database = _client[settings.MONGODB_DB_NAME]

    # Verify connection with a ping
    await _database.command("ping")
    _logger.info(f"MongoDB connected — db: {settings.MONGODB_DB_NAME}")


async def close_db() -> None:
    """
    Close the Motor connection gracefully.
    Called during FastAPI lifespan shutdown.
    """
    global _client, _database
    if _client is not None:
        _client.close()
        _client = None
        _database = None
        _logger.info("MongoDB connection closed")


def get_database() -> Optional[AsyncIOMotorDatabase]:  # type: ignore[type-arg]
    """
    Return the active database instance.
    Used by repositories and health checks.
    Returns None if not connected (e.g. during startup failure).
    """
    return _database


def get_collection(name: str):  # type: ignore[no-untyped-def]
    """
    Return a Motor collection by name.
    Convenience function for repositories.
    Raises RuntimeError if DB not connected.
    """
    if _database is None:
        raise RuntimeError("MongoDB database is not connected. Was connect_db() called?")
    return _database[name]
