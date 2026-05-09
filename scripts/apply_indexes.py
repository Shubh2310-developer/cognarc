#!/usr/bin/env python
"""
COGNARC — Idempotent MongoDB Index Application Script
scripts/apply_indexes.py

T3.1–T3.5: Apply all required indexes for all collections.
§08: Motor async driver. All indexes must exist before production queries run.

Usage:
    # From repo root with cognarc conda env active:
    source config/environments/.env.development
    python scripts/apply_indexes.py

    # Or via Makefile:
    make db-indexes

Idempotency: create_index() is a no-op if the index already exists with
the same name and definition. Safe to re-run at any time.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure the project's app package is importable when running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from motor.motor_asyncio import AsyncIOMotorClient

# ─── Connection ───────────────────────────────────────────────

MONGODB_URL = os.environ.get("MONGODB_URL", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "cognarc")

if not MONGODB_URL:
    print("[ERROR] MONGODB_URL is not set. Load .env first.", file=sys.stderr)
    sys.exit(1)


# ─── Index Definitions ────────────────────────────────────────

async def apply_indexes() -> None:
    """Apply all MongoDB indexes idempotently across all collections."""

    client: AsyncIOMotorClient = AsyncIOMotorClient(  # type: ignore[type-arg]
        MONGODB_URL,
        serverSelectionTimeoutMS=5000,
    )
    db = client[MONGODB_DB_NAME]

    try:
        # Verify connectivity
        await db.command("ping")
        print(f"[OK] Connected to MongoDB — db: {MONGODB_DB_NAME}")

        # ── users collection (T3.1) ───────────────────────────
        print("\n[users] Applying indexes...")

        # auth_id — unique (FK to Supabase auth.users)
        await db.users.create_index(
            "auth_id",
            unique=True,
            name="auth_id_unique",
        )
        print("  ✓ auth_id (unique)")

        # level — for leaderboard aggregation
        await db.users.create_index(
            "level",
            name="level_idx",
        )
        print("  ✓ level")

        # ── quests collection (T3.2) ─────────────────────────
        print("\n[quests] Applying indexes...")

        # (user_id, date) compound — daily quest fetch
        await db.quests.create_index(
            [("user_id", 1), ("date", -1)],
            name="user_date_compound",
        )
        print("  ✓ (user_id, date) compound")

        # status — pending quest queries
        await db.quests.create_index(
            "status",
            name="status_idx",
        )
        print("  ✓ status")

        # created_at — TTL 30 days (embedding expiry)
        # Note: TTL index fires ~60s after expiry; Atlas enforces this.
        await db.quests.create_index(
            "created_at",
            expireAfterSeconds=2_592_000,  # 30 days × 86400 seconds
            name="created_at_ttl_30d",
        )
        print("  ✓ created_at TTL (30d = 2,592,000s)")

        # ── progress_logs collection (T3.3 + T3.4) ───────────
        print("\n[progress_logs] Applying indexes...")

        # (user_id, completed_at) compound — user history queries
        await db.progress_logs.create_index(
            [("user_id", 1), ("completed_at", -1)],
            name="user_completed_at_compound",
        )
        print("  ✓ (user_id, completed_at) compound")

        # completed_at — TTL 90 days (archive expiry)
        await db.progress_logs.create_index(
            "completed_at",
            expireAfterSeconds=7_776_000,  # 90 days × 86400 seconds
            name="completed_at_ttl_90d",
        )
        print("  ✓ completed_at TTL (90d = 7,776,000s)")

        # ── streaks collection ────────────────────────────────
        print("\n[streaks] Applying indexes...")

        # user_id — unique, one streak doc per user
        await db.streaks.create_index(
            "user_id",
            unique=True,
            name="user_id_unique",
        )
        print("  ✓ user_id (unique)")

        print("\n[DONE] All indexes applied successfully.")

    finally:
        client.close()


# ─── Entry Point ─────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(apply_indexes())
