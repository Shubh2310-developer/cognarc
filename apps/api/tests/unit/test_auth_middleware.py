"""
COGNARC — Auth Middleware Unit Tests
apps/api/tests/unit/test_auth_middleware.py

§18: 100% coverage for JWT middleware accept/reject behaviour.
T2.9: Without token → 401; with valid token → 200.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../fixtures"))

import pytest
from conftest import *  # noqa: F401,F403

from app.middleware.auth import (
    decode_supabase_jwt,
    extract_bearer_token,
    is_public_path,
)


# ── extract_bearer_token ──────────────────────────────────────

class TestExtractBearerToken:
    def test_valid_bearer_returns_token(self):
        token = extract_bearer_token("Bearer my-test-token")
        assert token == "my-test-token"

    def test_none_header_returns_none(self):
        assert extract_bearer_token(None) is None

    def test_empty_header_returns_none(self):
        assert extract_bearer_token("") is None

    def test_malformed_no_bearer_returns_none(self):
        assert extract_bearer_token("Token abcdef") is None

    def test_only_bearer_word_returns_none(self):
        # "Bearer" with no token
        result = extract_bearer_token("Bearer ")
        # strip() on empty string gives ""
        assert result == "" or result is None


# ── is_public_path ────────────────────────────────────────────

class TestIsPublicPath:
    def test_health_is_public(self):
        assert is_public_path("/health") is True

    def test_health_ready_is_public(self):
        assert is_public_path("/health/ready") is True

    def test_health_live_is_public(self):
        assert is_public_path("/health/live") is True

    def test_auth_login_is_public(self):
        assert is_public_path("/api/v1/auth/login") is True

    def test_users_me_is_not_public(self):
        assert is_public_path("/api/v1/users/me") is False

    def test_quests_not_public(self):
        assert is_public_path("/api/v1/quests/today") is False


# ── decode_supabase_jwt ───────────────────────────────────────

class TestDecodeSupabaseJWT:
    def test_valid_token_decodes(self, valid_jwt_token):
        """Valid JWT should decode without raising."""
        payload = decode_supabase_jwt(valid_jwt_token)
        assert payload["sub"] == "test-user-uuid-1234"
        assert payload["email"] == "test@cognarc.app"

    def test_expired_token_raises_401(self, expired_jwt_token, test_client):
        """GET /users/me with expired token → 401."""
        response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_jwt_token}"},
        )
        assert response.status_code == 401

    def test_invalid_token_raises_401(self, invalid_jwt_token, test_client):
        """GET /users/me with wrong-secret token → 401."""
        response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {invalid_jwt_token}"},
        )
        assert response.status_code == 401

    def test_no_token_raises_401(self, test_client):
        """GET /users/me without any token → 401."""
        response = test_client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_malformed_bearer_raises_401(self, test_client):
        """Malformed Authorization header → 401."""
        response = test_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "NotBearer something"},
        )
        assert response.status_code == 401
