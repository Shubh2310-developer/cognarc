"""
COGNARC — pytest Fixtures
apps/api/tests/fixtures/conftest.py

Shared fixtures for all API tests.
§18: TestClient for integration tests.
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from jose import jwt

# Set test env before importing app
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("MONGODB_URL", "")  # Disable real MongoDB in unit tests
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret-key-for-testing-only-32chars")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")


@pytest.fixture(scope="session")
def test_client():
    """FastAPI TestClient for integration tests."""
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def valid_jwt_token():
    """Generate a valid test JWT that mimics a Supabase token."""
    secret = os.environ["SUPABASE_JWT_SECRET"]
    payload = {
        "sub": "test-user-uuid-1234",
        "email": "test@cognarc.app",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": "https://test.supabase.co/auth/v1",
        "exp": 9999999999,  # Far future expiry
        "iat": 1700000000,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Authorization headers with valid test JWT."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT to test 401 response."""
    secret = os.environ["SUPABASE_JWT_SECRET"]
    payload = {
        "sub": "test-user-uuid-expired",
        "email": "expired@cognarc.app",
        "role": "authenticated",
        "exp": 1000000000,  # Past expiry (2001)
        "iat": 1000000000,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def invalid_jwt_token():
    """A token signed with the wrong secret."""
    return jwt.encode({"sub": "hacker"}, "wrong-secret", algorithm="HS256")
