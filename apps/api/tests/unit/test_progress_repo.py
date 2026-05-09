"""
COGNARC — Unit Tests: Progress Repository
apps/api/tests/unit/test_progress_repo.py

Phase 02 validation gate:
  • create_log() inserts and returns ProgressLog
  • get_logs_for_user() returns sorted logs
  • get_completion_rate_7d() correct aggregation (0.0–1.0)
  • ensure_indexes() creates compound + TTL indexes
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId

from app.models.progress_log import ProgressLog


# ── Helpers ───────────────────────────────────────────────────

def _make_log(
    user_id: str = "507f1f77bcf86cd799439011",
    quest_id: str = "q_abc001",
    xp_earned: int = 100,
) -> ProgressLog:
    return ProgressLog(
        user_id=user_id,
        quest_id=quest_id,
        xp_earned=xp_earned,
        time_taken_min=25,
        evaluation_score=85.0,
    )


def _log_to_doc(log: ProgressLog) -> dict:
    doc = log.model_dump()
    doc["_id"] = ObjectId()
    return doc


def _make_async_cursor(docs: list):
    class _AsyncCursor:
        def __init__(self, items):
            self._items = items

        def __aiter__(self):
            return self._aiter_impl()

        async def _aiter_impl(self):
            for item in self._items:
                yield item

        def sort(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

    return _AsyncCursor(docs)


# ── create_log ────────────────────────────────────────────────

class TestCreateLog:
    @pytest.mark.asyncio
    async def test_create_log_returns_log(self):
        log = _make_log()
        doc = _log_to_doc(log)

        mock_col = MagicMock()
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=doc["_id"]))
        mock_col.find_one = AsyncMock(return_value=doc)

        with patch(
            "app.repositories.mongo.progress_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.progress_repository import create_log
            result = await create_log(log)

        assert result.quest_id == "q_abc001"
        assert result.xp_earned == 100
        assert result.evaluation_score == 85.0
        mock_col.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_log_self_report_no_score(self):
        log = ProgressLog(
            user_id="user1",
            quest_id="q_self",
            xp_earned=60,
            time_taken_min=20,
            evaluation_score=None,  # self-reported
        )
        doc = _log_to_doc(log)

        mock_col = MagicMock()
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=doc["_id"]))
        mock_col.find_one = AsyncMock(return_value=doc)

        with patch(
            "app.repositories.mongo.progress_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.progress_repository import create_log
            result = await create_log(log)

        assert result.evaluation_score is None


# ── get_logs_for_user ─────────────────────────────────────────

class TestGetLogsForUser:
    @pytest.mark.asyncio
    async def test_returns_all_logs(self):
        logs = [_make_log(quest_id=f"q_{i}") for i in range(5)]
        docs = [_log_to_doc(l) for l in logs]
        cursor = _make_async_cursor(docs)

        mock_col = MagicMock()
        mock_col.find = MagicMock(return_value=cursor)

        with patch(
            "app.repositories.mongo.progress_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.progress_repository import get_logs_for_user
            result = await get_logs_for_user("user123", limit=10)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_logs(self):
        cursor = _make_async_cursor([])

        mock_col = MagicMock()
        mock_col.find = MagicMock(return_value=cursor)

        with patch(
            "app.repositories.mongo.progress_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.progress_repository import get_logs_for_user
            result = await get_logs_for_user("no_user", limit=10)

        assert result == []


# ── get_completion_rate_7d ────────────────────────────────────

class TestGetCompletionRate7d:
    @pytest.mark.asyncio
    async def test_completion_rate_correct(self):
        """4 completed out of 5 attempted = 0.8 completion rate."""
        mock_progress_col = MagicMock()
        mock_progress_col.count_documents = AsyncMock(return_value=4)

        mock_quests_col = MagicMock()
        mock_quests_col.count_documents = AsyncMock(return_value=5)

        def _col_factory(name: str):
            if name == "progress_logs":
                return mock_progress_col
            elif name == "quests":
                return mock_quests_col
            raise ValueError(f"Unexpected collection: {name}")

        with (
            patch("app.repositories.mongo.progress_repository._get_col", return_value=mock_progress_col),
            patch("app.db.mongodb.get_collection", side_effect=_col_factory),
        ):
            from app.repositories.mongo.progress_repository import get_completion_rate_7d
            rate = await get_completion_rate_7d("user123")

        assert rate == pytest.approx(0.8, abs=0.01)

    @pytest.mark.asyncio
    async def test_completion_rate_zero_when_no_quests(self):
        """0 completed, 0 total → rate = 0.0."""
        mock_progress_col = MagicMock()
        mock_progress_col.count_documents = AsyncMock(return_value=0)

        mock_quests_col = MagicMock()
        mock_quests_col.count_documents = AsyncMock(return_value=0)

        def _col_factory(name: str):
            if name == "quests":
                return mock_quests_col
            return mock_progress_col

        with (
            patch("app.repositories.mongo.progress_repository._get_col", return_value=mock_progress_col),
            patch("app.db.mongodb.get_collection", side_effect=_col_factory),
        ):
            from app.repositories.mongo.progress_repository import get_completion_rate_7d
            rate = await get_completion_rate_7d("no_quests_user")

        assert rate == 0.0

    @pytest.mark.asyncio
    async def test_completion_rate_capped_at_1(self):
        """Rate is always clamped to [0.0, 1.0]."""
        mock_progress_col = MagicMock()
        mock_progress_col.count_documents = AsyncMock(return_value=10)

        mock_quests_col = MagicMock()
        mock_quests_col.count_documents = AsyncMock(return_value=5)

        def _col_factory(name: str):
            if name == "quests":
                return mock_quests_col
            return mock_progress_col

        with (
            patch("app.repositories.mongo.progress_repository._get_col", return_value=mock_progress_col),
            patch("app.db.mongodb.get_collection", side_effect=_col_factory),
        ):
            from app.repositories.mongo.progress_repository import get_completion_rate_7d
            rate = await get_completion_rate_7d("over_achiever")

        assert rate <= 1.0


# ── ensure_indexes ────────────────────────────────────────────

class TestProgressEnsureIndexes:
    @pytest.mark.asyncio
    async def test_creates_compound_and_ttl_indexes(self):
        mock_col = MagicMock()
        mock_col.create_index = AsyncMock(return_value="idx")

        with patch(
            "app.repositories.mongo.progress_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.progress_repository import ensure_indexes
            await ensure_indexes()

        # Compound (user_id, completed_at) + TTL on completed_at
        assert mock_col.create_index.call_count == 2

        calls = mock_col.create_index.call_args_list
        # First call: compound index (list of tuples)
        assert isinstance(calls[0][0][0], list)
        # Second call: TTL index (string)
        assert calls[1][0][0] == "completed_at"
        assert calls[1][1].get("expireAfterSeconds") == 7_776_000
