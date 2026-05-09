#!/usr/bin/env python
"""
COGNARC — Seed Test User
data/seed/seed_user.py

T6.2: Insert a fully-populated test user into MongoDB for frontend dev / integration testing.
      Idempotent — skips if user with same auth_id already exists.

Usage (from repo root, cognarc conda env active):
    source config/environments/.env.development
    python data/seed/seed_user.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Make app importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api"))

import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError

MONGODB_URL = os.environ.get("MONGODB_URL", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "cognarc")

if not MONGODB_URL:
    print("[ERROR] MONGODB_URL not set. Load .env first.", file=sys.stderr)
    sys.exit(1)

# ── Seed Payload ──────────────────────────────────────────────

SEED_USER = {
    "auth_id": "00000000-0000-0000-0000-000000000001",  # Fake Supabase UUID
    "username": "dev_agent",
    "email": "dev@cognarc.local",
    "avatar_url": None,
    "level": 3,
    "total_xp": 875,
    "active_skill_tree": "AI Engineering",
    "skill_state": {
        "AI Engineering": {
            "current_node": "ml-fundamentals",
            "node_progress": 0.45,
            "mastered_nodes": ["python-basics", "python-oop"],
            "unlocked_nodes": ["python-advanced", "numpy-pandas", "ml-fundamentals"],
            "locked_nodes": [
                "deep-learning", "llm-fundamentals", "rag-systems",
                "ai-agents", "mlops", "ai-engineering-boss"
            ]
        }
    },
    "behavioral_profile": {
        "difficulty_modifier": 1.1,
        "preferred_quest_types": ["coding", "build"],
        "completion_rate_7d": 0.82,
        "mode": "normal",
        "avg_time_per_quest_min": 28.5,
        "boredom_signal": 1.5,
        "frustration_signal": 0.5
    },
    "settings": {
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "daily_goal_quests": 3,
        "notifications_enabled": True
    }
}


async def seed_user() -> None:
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGODB_URL, serverSelectionTimeoutMS=5000
    )
    db = client[MONGODB_DB_NAME]

    try:
        await db.command("ping")
        print(f"[OK] Connected to MongoDB — db: {MONGODB_DB_NAME}")

        existing = await db.users.find_one({"auth_id": SEED_USER["auth_id"]})
        if existing:
            print(f"[SKIP] User '{SEED_USER['username']}' already exists (auth_id: {SEED_USER['auth_id']})")
            return

        from datetime import datetime, timezone
        SEED_USER["created_at"] = datetime.now(timezone.utc)
        SEED_USER["updated_at"] = datetime.now(timezone.utc)

        result = await db.users.insert_one(SEED_USER.copy())
        print(f"[OK] Seed user inserted — _id: {result.inserted_id}")
        print(f"     username    : {SEED_USER['username']}")
        print(f"     auth_id     : {SEED_USER['auth_id']}")
        print(f"     level       : {SEED_USER['level']}")
        print(f"     total_xp    : {SEED_USER['total_xp']}")
        print(f"     active_tree : {SEED_USER['active_skill_tree']}")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_user())
