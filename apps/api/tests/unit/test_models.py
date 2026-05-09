"""
COGNARC — Unit Tests: Pydantic Domain Models
apps/api/tests/unit/test_models.py

Phase 02 validation gate:
  • User / SkillState / BehavioralProfile / UserSettings reject extra fields
  • Quest / EvaluationCriteria validation
  • ProgressLog / Streak creation and defaults
  • extra="forbid" enforced on all primary domain models
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.models.user import BehavioralProfile, SkillState, User, UserSettings
from app.models.quest import EvaluationCriteria, Quest
from app.models.progress_log import ProgressLog
from app.models.streak import Streak


# ── Helpers ───────────────────────────────────────────────────

def _valid_user_kwargs() -> dict:
    return {
        "auth_id": "aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb",
        "username": "test_user",
        "email": "test@cognarc.app",
    }


def _valid_quest_kwargs(user_id: str = "507f1f77bcf86cd799439011") -> dict:
    return {
        "quest_id": "q_abc1234567",
        "user_id": user_id,
        "date": datetime.now(timezone.utc),
        "title": "Build a Binary Search",
        "description": "Implement binary search on a sorted list.",
        "type": "coding",
        "difficulty": "easy",
        "estimated_minutes": 30,
        "xp_reward": 75,
        "skill_node": "python-advanced",
        "skill_tree": "AI Engineering",
        "evaluation_criteria": EvaluationCriteria(
            type="code_submission", test_cases=3, pass_threshold=0.67
        ),
        "created_at": datetime.now(timezone.utc),
    }


# ── SkillState ────────────────────────────────────────────────

class TestSkillState:
    def test_valid_creation(self):
        s = SkillState(current_node="python-basics")
        assert s.current_node == "python-basics"
        assert s.node_progress == 0.0
        assert s.mastered_nodes == []

    def test_progress_clamped(self):
        with pytest.raises(ValidationError):
            SkillState(current_node="x", node_progress=1.5)  # > 1.0

    def test_extra_field_forbidden(self):
        """§17: extra='forbid' must reject unknown fields."""
        with pytest.raises(ValidationError):
            SkillState(current_node="x", unknown_field="bad")


# ── BehavioralProfile ─────────────────────────────────────────

class TestBehavioralProfile:
    def test_defaults(self):
        bp = BehavioralProfile()
        assert bp.difficulty_modifier == 1.0
        assert bp.mode == "normal"
        assert bp.preferred_quest_types == []

    def test_modifier_bounds(self):
        with pytest.raises(ValidationError):
            BehavioralProfile(difficulty_modifier=0.1)  # < 0.5
        with pytest.raises(ValidationError):
            BehavioralProfile(difficulty_modifier=3.0)  # > 2.0

    def test_valid_mode_literals(self):
        for mode in ("normal", "comeback", "boredom", "frustration"):
            bp = BehavioralProfile(mode=mode)
            assert bp.mode == mode

    def test_invalid_mode(self):
        with pytest.raises(ValidationError):
            BehavioralProfile(mode="rage")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            BehavioralProfile(mystery_field=42)


# ── UserSettings ──────────────────────────────────────────────

class TestUserSettings:
    def test_defaults(self):
        s = UserSettings()
        assert s.timezone == "UTC"
        assert s.theme == "dark"
        assert s.daily_goal_quests == 3

    def test_theme_validation(self):
        with pytest.raises(ValidationError):
            UserSettings(theme="blue")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            UserSettings(colour_scheme="purple")


# ── User ──────────────────────────────────────────────────────

class TestUser:
    def test_valid_creation(self):
        u = User(**_valid_user_kwargs())
        assert u.level == 1
        assert u.total_xp == 0
        assert u.active_skill_tree == "AI Engineering"
        assert isinstance(u.behavioral_profile, BehavioralProfile)
        assert isinstance(u.settings, UserSettings)

    def test_extra_field_forbidden(self):
        """§17 rule: User must reject extra fields."""
        with pytest.raises(ValidationError):
            User(**_valid_user_kwargs(), hack="inject")

    def test_invalid_email(self):
        kwargs = _valid_user_kwargs()
        kwargs["email"] = "not-an-email"
        with pytest.raises(ValidationError):
            User(**kwargs)

    def test_total_xp_nonnegative(self):
        with pytest.raises(ValidationError):
            User(**_valid_user_kwargs(), total_xp=-100)

    def test_skill_state_nested(self):
        state = SkillState(current_node="python-basics")
        u = User(**_valid_user_kwargs(), skill_state={"AI Engineering": state})
        assert u.skill_state["AI Engineering"].current_node == "python-basics"

    def test_timestamps_set_on_creation(self):
        u = User(**_valid_user_kwargs())
        assert u.created_at is not None
        assert u.updated_at is not None


# ── EvaluationCriteria ────────────────────────────────────────

class TestEvaluationCriteria:
    def test_valid_types(self):
        for t in ("code_submission", "self_report", "theory_qa"):
            ec = EvaluationCriteria(type=t)
            assert ec.type == t

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            EvaluationCriteria(type="vibes_only")

    def test_threshold_bounds(self):
        with pytest.raises(ValidationError):
            EvaluationCriteria(type="self_report", pass_threshold=1.5)

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            EvaluationCriteria(type="self_report", mystery="x")


# ── Quest ─────────────────────────────────────────────────────

class TestQuest:
    def test_valid_creation(self):
        q = Quest(**_valid_quest_kwargs())
        assert q.status == "pending"
        assert q.generated_by == "groq"
        assert q.embedding == []
        assert q.completed_at is None

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Quest(**_valid_quest_kwargs(), sneaky_field="bad")

    def test_invalid_type(self):
        kwargs = _valid_quest_kwargs()
        kwargs["type"] = "vibing"
        with pytest.raises(ValidationError):
            Quest(**kwargs)

    def test_invalid_difficulty(self):
        kwargs = _valid_quest_kwargs()
        kwargs["difficulty"] = "legendary"
        with pytest.raises(ValidationError):
            Quest(**kwargs)

    def test_xp_nonnegative(self):
        kwargs = _valid_quest_kwargs()
        kwargs["xp_reward"] = -10
        with pytest.raises(ValidationError):
            Quest(**kwargs)

    def test_embedding_defaults_empty(self):
        q = Quest(**_valid_quest_kwargs())
        assert q.embedding == []


# ── ProgressLog ───────────────────────────────────────────────

class TestProgressLog:
    def test_valid_creation(self):
        log = ProgressLog(
            user_id="507f1f77bcf86cd799439011",
            quest_id="q_abc123",
            xp_earned=100,
            time_taken_min=25,
        )
        assert log.evaluation_score is None
        assert log.evaluation_method == "self_report"
        assert log.xp_earned == 100

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            ProgressLog(
                user_id="x", quest_id="y",
                xp_earned=10, time_taken_min=5,
                hidden_field="bad"
            )

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            ProgressLog(
                user_id="x", quest_id="y",
                xp_earned=10, time_taken_min=5,
                evaluation_score=150.0  # > 100
            )

    def test_xp_nonnegative(self):
        with pytest.raises(ValidationError):
            ProgressLog(user_id="x", quest_id="y", xp_earned=-5, time_taken_min=5)


# ── Streak ────────────────────────────────────────────────────

class TestStreak:
    def test_valid_creation(self):
        s = Streak(user_id="507f1f77bcf86cd799439011")
        assert s.current_streak == 0
        assert s.longest_streak == 0
        assert s.shield_count == 0
        assert s.last_completion_date is None

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Streak(user_id="x", bonus_field="nope")

    def test_streak_nonnegative(self):
        with pytest.raises(ValidationError):
            Streak(user_id="x", current_streak=-1)
