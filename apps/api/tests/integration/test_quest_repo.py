"""
COGNARC — Integration Tests: Quest Repository
apps/api/tests/integration/test_quest_repo.py

Phase 02 validation gate:
  • create_quest() inserts and returns Quest
  • get_quest_by_id() fetches by quest_id field
  • update_quest_status() sets status and completed_at
  • get_quests_for_user_today() uses compound index (user_id, date)
  • get_recent_quests() filters by date range
  • ensure_indexes() creates all required indexes
"""
from __future__ import annotations

import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId

from app.models.quest import EvaluationCriteria, Quest


# ── Helpers ───────────────────────────────────────────────────

def _make_quest(
    quest_id: str = "q_test001",
    user_id: str = "507f1f77bcf86cd799439011",
    status: str = "pending",
) -> Quest:
    return Quest(
        quest_id=quest_id,
        user_id=user_id,
        date=datetime.now(timezone.utc),
        title="Repo Test Quest",
        description="A quest for testing the repository layer.",
        type="coding",
        difficulty="easy",
        estimated_minutes=30,
        xp_reward=75,
        skill_node="python-basics",
        skill_tree="AI Engineering",
        evaluation_criteria=EvaluationCriteria(type="code_submission", test_cases=2),
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def _quest_to_doc(quest: Quest) -> dict:
    doc = quest.model_dump()
    doc["_id"] = ObjectId()
    return doc


def _make_async_cursor(docs: list) -> MagicMock:
    """Return a mock async cursor that yields docs via async for."""
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


# ── create_quest ──────────────────────────────────────────────

class TestCreateQuest:
    @pytest.mark.asyncio
    async def test_create_quest_returns_quest(self):
        quest = _make_quest()
        doc = _quest_to_doc(quest)

        mock_col = MagicMock()
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=doc["_id"]))
        mock_col.find_one = AsyncMock(return_value=doc)

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import create_quest
            result = await create_quest(quest)

        assert result.quest_id == "q_test001"
        assert result.status == "pending"
        mock_col.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_quest_stores_evaluation_criteria(self):
        quest = _make_quest()
        doc = _quest_to_doc(quest)

        mock_col = MagicMock()
        mock_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=doc["_id"]))
        mock_col.find_one = AsyncMock(return_value=doc)

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import create_quest
            result = await create_quest(quest)

        assert result.evaluation_criteria.type == "code_submission"
        assert result.evaluation_criteria.test_cases == 2


# ── get_quest_by_id ───────────────────────────────────────────

class TestGetQuestById:
    @pytest.mark.asyncio
    async def test_returns_quest_on_hit(self):
        quest = _make_quest("q_fetch001")
        doc = _quest_to_doc(quest)

        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=doc)

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import get_quest_by_id
            result = await get_quest_by_id("q_fetch001")

        assert result is not None
        assert result.quest_id == "q_fetch001"
        mock_col.find_one.assert_called_once_with({"quest_id": "q_fetch001"})

    @pytest.mark.asyncio
    async def test_returns_none_on_miss(self):
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=None)

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import get_quest_by_id
            result = await get_quest_by_id("q_nonexistent")

        assert result is None


# ── update_quest_status ───────────────────────────────────────

class TestUpdateQuestStatus:
    @pytest.mark.asyncio
    async def test_update_to_completed_sets_completed_at(self):
        mock_col = MagicMock()
        mock_col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import update_quest_status
            await update_quest_status("q_complete001", "completed")

        mock_col.update_one.assert_called_once()
        update_doc = mock_col.update_one.call_args[0][1]
        assert update_doc["$set"]["status"] == "completed"
        assert "completed_at" in update_doc["$set"]

    @pytest.mark.asyncio
    async def test_update_to_skipped_no_completed_at(self):
        mock_col = MagicMock()
        mock_col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import update_quest_status
            await update_quest_status("q_skip001", "skipped")

        update_doc = mock_col.update_one.call_args[0][1]
        assert update_doc["$set"]["status"] == "skipped"
        assert "completed_at" not in update_doc["$set"]


# ── get_quests_for_user_today (compound index) ────────────────

class TestGetQuestsForUserToday:
    @pytest.mark.asyncio
    async def test_returns_todays_quests(self):
        """Uses compound index (user_id, date). Verify query filter shape."""
        quest = _make_quest("q_today")
        doc = _quest_to_doc(quest)
        cursor = _make_async_cursor([doc])

        mock_col = MagicMock()
        mock_col.find = MagicMock(return_value=cursor)

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import get_quests_for_user_today
            result = await get_quests_for_user_today("507f1f77bcf86cd799439011", date.today())

        assert len(result) == 1
        assert result[0].quest_id == "q_today"

        # Verify the compound index query filter shape
        call_filter = mock_col.find.call_args[0][0]
        assert "user_id" in call_filter
        assert "date" in call_filter
        assert "$gte" in call_filter["date"]
        assert "$lt" in call_filter["date"]

    @pytest.mark.asyncio
    async def test_returns_empty_list_no_quests(self):
        cursor = _make_async_cursor([])
        mock_col = MagicMock()
        mock_col.find = MagicMock(return_value=cursor)

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import get_quests_for_user_today
            result = await get_quests_for_user_today("no_user", date.today())

        assert result == []


# ── get_recent_quests ─────────────────────────────────────────

class TestGetRecentQuests:
    @pytest.mark.asyncio
    async def test_returns_recent_quests(self):
        quests = [_make_quest(f"q_recent_{i}") for i in range(3)]
        docs = [_quest_to_doc(q) for q in quests]
        cursor = _make_async_cursor(docs)

        mock_col = MagicMock()
        mock_col.find = MagicMock(return_value=cursor)

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import get_recent_quests
            result = await get_recent_quests("user123", days=7)

        assert len(result) == 3
        # Verify date filter applied
        call_filter = mock_col.find.call_args[0][0]
        assert "date" in call_filter
        assert "$gte" in call_filter["date"]


# ── ensure_indexes ────────────────────────────────────────────

class TestQuestEnsureIndexes:
    @pytest.mark.asyncio
    async def test_ensure_indexes_creates_all_three(self):
        mock_col = MagicMock()
        mock_col.create_index = AsyncMock(return_value="idx")

        with patch(
            "app.repositories.mongo.quest_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.quest_repository import ensure_indexes
            await ensure_indexes()

        # Should create 3 indexes: compound, status, TTL
        assert mock_col.create_index.call_count == 3

        calls = [c[0][0] for c in mock_col.create_index.call_args_list]
        # compound index is a list of tuples
        assert any(isinstance(c, list) for c in calls), "Expected compound index"
        # status and created_at are strings
        str_calls = [c for c in calls if isinstance(c, str)]
        assert "status" in str_calls
        assert "created_at" in str_calls
