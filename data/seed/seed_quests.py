#!/usr/bin/env python
"""
COGNARC — Seed Sample Quests
data/seed/seed_quests.py

T6.3: Insert 3 sample quests for the seed user (dev_agent) for frontend dev testing.
      Idempotent — clears existing pending quests for today before inserting.

Usage (from repo root, cognarc conda env active):
    source config/environments/.env.development
    python data/seed/seed_quests.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "api"))

import motor.motor_asyncio

MONGODB_URL = os.environ.get("MONGODB_URL", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "cognarc")

if not MONGODB_URL:
    print("[ERROR] MONGODB_URL not set. Load .env first.", file=sys.stderr)
    sys.exit(1)

SEED_USER_AUTH_ID = "00000000-0000-0000-0000-000000000001"


def make_quest_id() -> str:
    return f"q_{uuid.uuid4().hex[:10]}"


SEED_QUESTS = [
    {
        "quest_id": make_quest_id(),
        "date": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
        "title": "Implement a Python LRU Cache",
        "description": (
            "Build a least-recently-used cache class in pure Python using `OrderedDict`. "
            "It must support `get(key)` and `put(key, value)` operations in O(1) time. "
            "Add a `capacity` parameter capping the total entries."
        ),
        "type": "coding",
        "difficulty": "medium",
        "estimated_minutes": 35,
        "xp_reward": 110,
        "skill_node": "python-advanced",
        "skill_tree": "AI Engineering",
        "evaluation_criteria": {
            "type": "code_submission",
            "test_cases": 3,
            "pass_threshold": 0.67
        },
        "hints": [
            "OrderedDict preserves insertion order — use `move_to_end()` on access.",
            "Track capacity with `len(self.cache)` before inserting."
        ],
        "embedding": [],
        "status": "pending",
        "generated_by": "cached",
        "completed_at": None
    },
    {
        "quest_id": make_quest_id(),
        "date": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
        "title": "Explain the Bias–Variance Trade-off",
        "description": (
            "Write a concise explanation (≥200 words) covering: "
            "(1) what bias and variance are, "
            "(2) how they relate to underfitting and overfitting, "
            "(3) how to diagnose each using learning curves, and "
            "(4) one concrete technique to reduce each."
        ),
        "type": "theory",
        "difficulty": "easy",
        "estimated_minutes": 20,
        "xp_reward": 60,
        "skill_node": "ml-fundamentals",
        "skill_tree": "AI Engineering",
        "evaluation_criteria": {
            "type": "self_report",
            "test_cases": 0,
            "pass_threshold": 1.0
        },
        "hints": [
            "Think about what happens as model complexity increases from left to right.",
            "Regularisation (L1/L2) reduces variance. More data reduces both."
        ],
        "embedding": [],
        "status": "pending",
        "generated_by": "cached",
        "completed_at": None
    },
    {
        "quest_id": make_quest_id(),
        "date": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
        "title": "Debug a Broken Pandas Merge",
        "description": (
            "Given two DataFrames with mismatched dtypes on the join key, "
            "identify and fix the bug that causes a cartesian product instead of a proper left join. "
            "Reduce the output from 1200 rows to the expected 40 rows."
        ),
        "type": "debug",
        "difficulty": "easy",
        "estimated_minutes": 25,
        "xp_reward": 75,
        "skill_node": "numpy-pandas",
        "skill_tree": "AI Engineering",
        "evaluation_criteria": {
            "type": "code_submission",
            "test_cases": 2,
            "pass_threshold": 1.0
        },
        "hints": [
            "Check `df.dtypes` on both DataFrames before merging.",
            "Use `.astype(str)` or `.astype(int)` to align types on the key column."
        ],
        "embedding": [],
        "status": "pending",
        "generated_by": "cached",
        "completed_at": None
    }
]


async def seed_quests() -> None:
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGODB_URL, serverSelectionTimeoutMS=5000
    )
    db = client[MONGODB_DB_NAME]

    try:
        await db.command("ping")
        print(f"[OK] Connected to MongoDB — db: {MONGODB_DB_NAME}")

        # Resolve the user's MongoDB _id from auth_id
        user_doc = await db.users.find_one({"auth_id": SEED_USER_AUTH_ID})
        if user_doc is None:
            print("[ERROR] Seed user not found. Run seed_user.py first.")
            return

        user_id = str(user_doc["_id"])
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Remove today's existing pending quests for this user (idempotency)
        deleted = await db.quests.delete_many(
            {"user_id": user_id, "date": today_start, "status": "pending"}
        )
        if deleted.deleted_count:
            print(f"[CLEAN] Removed {deleted.deleted_count} existing pending quests for today.")

        # Inject user_id and created_at
        now = datetime.now(timezone.utc)
        docs = []
        for q in SEED_QUESTS:
            doc = q.copy()
            doc["user_id"] = user_id
            doc["created_at"] = now
            docs.append(doc)

        result = await db.quests.insert_many(docs)
        print(f"[OK] Inserted {len(result.inserted_ids)} seed quests for user '{user_doc.get('username', user_id)}'")

        for q, _id in zip(SEED_QUESTS, result.inserted_ids):
            print(f"  • [{q['type'].upper():8}] {q['title']} — {q['xp_reward']} XP ({q['difficulty']})")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_quests())
