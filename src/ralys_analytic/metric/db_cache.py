"""
db_cache.py - SQLite cache layer for Moralis API responses.

If cached data exists and is less than 6 hours old, returns it from DB.
Otherwise calls the Moralis API, stores the result, and returns fresh data.
Falls back gracefully to direct API calls if the database is unreachable.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 6

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "cache.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def initialize_tables():
    create_sql = """
    CREATE TABLE IF NOT EXISTS api_cache (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type        TEXT NOT NULL,
        token_name       TEXT NOT NULL,
        contract_address TEXT NOT NULL,
        chain            TEXT NOT NULL,
        response_data    TEXT NOT NULL,
        fetched_at       TEXT NOT NULL,
        UNIQUE (data_type, token_name)
    );

    CREATE INDEX IF NOT EXISTS idx_cache_lookup
        ON api_cache (data_type, token_name);

    CREATE INDEX IF NOT EXISTS idx_cache_freshness
        ON api_cache (data_type, fetched_at);
    """
    try:
        conn = _get_connection()
        conn.executescript(create_sql)
        conn.close()
        logger.info("Cache tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize cache tables: {e}")
        raise


def get_cached_data(data_type: str, token_name: str) -> Optional[Dict[str, Any]]:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
    query = """
    SELECT response_data, fetched_at
    FROM api_cache
    WHERE data_type = ? AND token_name = ? AND fetched_at > ?
    LIMIT 1;
    """
    try:
        conn = _get_connection()
        cur = conn.execute(query, (data_type, token_name, cutoff))
        row = cur.fetchone()
        conn.close()
        if row:
            logger.info(f"Cache HIT for {data_type}/{token_name} (fetched at {row[1]})")
            return json.loads(row[0])
        else:
            logger.info(f"Cache MISS for {data_type}/{token_name}")
            return None
    except Exception as e:
        logger.error(f"Cache read failed for {data_type}/{token_name}: {e}")
        return None


def update_cache(
    data_type: str,
    token_name: str,
    contract_address: str,
    chain: str,
    data: Dict[str, Any],
) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    upsert_sql = """
    INSERT INTO api_cache (data_type, token_name, contract_address, chain, response_data, fetched_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT (data_type, token_name)
    DO UPDATE SET
        response_data = excluded.response_data,
        contract_address = excluded.contract_address,
        chain = excluded.chain,
        fetched_at = excluded.fetched_at;
    """
    try:
        conn = _get_connection()
        conn.execute(
            upsert_sql,
            (data_type, token_name, contract_address, chain, json.dumps(data), now),
        )
        conn.commit()
        conn.close()
        logger.info(f"Cache UPDATED for {data_type}/{token_name}")
        return True
    except Exception as e:
        logger.error(f"Cache write failed for {data_type}/{token_name}: {e}")
        return False


def get_cache_fetched_at(data_type: str, token_name: str) -> Optional[str]:
    """Return the fetched_at ISO timestamp for a cached entry, or None if not found."""
    query = """
    SELECT fetched_at FROM api_cache
    WHERE data_type = ? AND token_name = ?
    LIMIT 1;
    """
    try:
        conn = _get_connection()
        cur = conn.execute(query, (data_type, token_name))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Cache fetched_at lookup failed for {data_type}/{token_name}: {e}")
        return None


def get_or_fetch(
    data_type: str,
    token_name: str,
    contract_address: str,
    chain: str,
    fetch_fn: Callable[[], Dict[str, Any]],
) -> Dict[str, Any]:
    # Try cache first
    try:
        cached = get_cached_data(data_type, token_name)
        if cached is not None:
            return cached
    except Exception as e:
        logger.warning(f"Cache lookup failed, falling back to API: {e}")

    # Fetch fresh data from Moralis
    fresh_data = fetch_fn()

    # Store in cache (skip if API returned an error)
    if fresh_data and "error" not in fresh_data:
        try:
            update_cache(data_type, token_name, contract_address, chain, fresh_data)
        except Exception as e:
            logger.warning(f"Cache store failed (data still returned): {e}")

    return fresh_data
