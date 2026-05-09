"""
COGNARC — Integration Tests: User Repository
apps/api/tests/integration/test_user_repo.py

Phase 02 validation gate:
  • create_user() inserts and returns correct User
  • get_user_by_auth_id() returns correct doc
  • get_user_by_id() works with valid ObjectId
  • update_user() patches specified fields
  • update_skill_state() updates nested skill_state map
  • Returns None for missing users (no exception)

NOTE: These tests use mongomock to avoid requiring a live MongoDB connection.
      mongomock patches motor at the collection level.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId

from app.models.user import BehavioralProfile, SkillState, User, UserSettings


# ── Helpers ───────────────────────────────────────────────────

def _make_user(auth_id: str = "auth-uuid-001") -> User:
    return User(
        auth_id=auth_id,
        username="test_agent",
        email="agent@example.com",
    )


def _user_to_doc(user: User, _id: ObjectId | None = None) -> dict:
    doc = user.model_dump()
    doc["_id"] = _id or ObjectId()
    return doc


# ── Mock collection factory ───────────────────────────────────

def _mock_col_with_doc(doc: dict) -> MagicMock:
    """Return a mocked Motor collection that returns `doc` on find_one."""
    col = MagicMock()
    col.find_one = AsyncMock(return_value=doc)
    col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=doc["_id"]))
    col.find_one_and_update = AsyncMock(return_value=doc)
    col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    col.create_index = AsyncMock(return_value="index_name")
    return col


# ── create_user ───────────────────────────────────────────────

class TestCreateUser:
    @pytest.mark.asyncio
    async def test_create_user_returns_user(self):
        user = _make_user("auth-001")
        doc = _user_to_doc(user)
        mock_col = _mock_col_with_doc(doc)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import create_user
            result = await create_user(user)

        assert result.auth_id == "auth-001"
        assert result.username == "test_agent"
        assert result.level == 1
        assert result.total_xp == 0

    @pytest.mark.asyncio
    async def test_create_user_calls_insert_once(self):
        user = _make_user("auth-002")
        doc = _user_to_doc(user)
        mock_col = _mock_col_with_doc(doc)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import create_user
            await create_user(user)

        mock_col.insert_one.assert_called_once()


# ── get_user_by_auth_id ───────────────────────────────────────

class TestGetUserByAuthId:
    @pytest.mark.asyncio
    async def test_returns_correct_user(self):
        user = _make_user("auth-003")
        doc = _user_to_doc(user)
        mock_col = _mock_col_with_doc(doc)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import get_user_by_auth_id
            result = await get_user_by_auth_id("auth-003")

        assert result is not None
        assert result.auth_id == "auth-003"
        mock_col.find_one.assert_called_once_with({"auth_id": "auth-003"})

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=None)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import get_user_by_auth_id
            result = await get_user_by_auth_id("nonexistent-auth")

        assert result is None


# ── get_user_by_id ────────────────────────────────────────────

class TestGetUserById:
    @pytest.mark.asyncio
    async def test_returns_user_for_valid_id(self):
        user = _make_user("auth-004")
        oid = ObjectId()
        doc = _user_to_doc(user, _id=oid)
        mock_col = _mock_col_with_doc(doc)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import get_user_by_id
            result = await get_user_by_id(str(oid))

        assert result is not None
        assert result.auth_id == "auth-004"

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_objectid(self):
        mock_col = MagicMock()

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import get_user_by_id
            result = await get_user_by_id("not-a-valid-objectid")

        assert result is None
        mock_col.find_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=None)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import get_user_by_id
            result = await get_user_by_id(str(ObjectId()))

        assert result is None


# ── update_user ───────────────────────────────────────────────

class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_update_user_sets_fields(self):
        user = _make_user("auth-005")
        oid = ObjectId()
        doc = _user_to_doc(user, _id=oid)
        doc["username"] = "updated_agent"

        mock_col = _mock_col_with_doc(doc)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import update_user
            result = await update_user(str(oid), {"username": "updated_agent"})

        assert result.username == "updated_agent"
        mock_col.find_one_and_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_raises_on_not_found(self):
        mock_col = MagicMock()
        mock_col.find_one_and_update = AsyncMock(return_value=None)

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import update_user
            with pytest.raises(ValueError, match="not found"):
                await update_user(str(ObjectId()), {"level": 5})


# ── update_skill_state ────────────────────────────────────────

class TestUpdateSkillState:
    @pytest.mark.asyncio
    async def test_update_skill_state_calls_update_one(self):
        mock_col = MagicMock()
        mock_col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        oid = ObjectId()

        state = SkillState(
            current_node="ml-fundamentals",
            node_progress=0.5,
            mastered_nodes=["python-basics"],
        )

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import update_skill_state
            await update_skill_state(str(oid), "AI Engineering", state)

        mock_col.update_one.assert_called_once()
        call_filter = mock_col.update_one.call_args[0][0]
        assert call_filter == {"_id": oid}

        call_update = mock_col.update_one.call_args[0][1]
        assert "skill_state.AI Engineering" in call_update["$set"]


# ── ensure_indexes ────────────────────────────────────────────

class TestEnsureIndexes:
    @pytest.mark.asyncio
    async def test_ensure_indexes_called(self):
        mock_col = MagicMock()
        mock_col.create_index = AsyncMock(return_value="idx")

        with patch(
            "app.repositories.mongo.user_repository._get_col",
            return_value=mock_col,
        ):
            from app.repositories.mongo.user_repository import ensure_indexes
            await ensure_indexes()

        assert mock_col.create_index.call_count == 2
        # First call: auth_id unique
        first_call = mock_col.create_index.call_args_list[0]
        assert first_call[0][0] == "auth_id"
        assert first_call[1].get("unique") is True
