"""
COGNARC — Health Endpoint Tests
apps/api/tests/integration/test_health.py

§18: 100% coverage target for health endpoints.
T1.15 validation: GET /health → 200 {"status":"ok"}
"""
from __future__ import annotations

import sys
import os

# Add fixture path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../fixtures"))

import pytest
from conftest import *  # noqa: F401,F403


class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    def test_health_returns_200(self, test_client):
        """GET /health must return 200 with status:ok"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_health_live_returns_200(self, test_client):
        """GET /health/live must return 200"""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_health_ready_returns_status(self, test_client):
        """
        GET /health/ready returns either 200 (DB connected) or 503 (DB down).
        In test environment with no DB, it returns 503.
        We validate the response shape, not the exact status.
        """
        response = test_client.get("/health/ready")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "database" in data
        assert data["database"] in ("connected", "disconnected")

    def test_health_does_not_require_auth(self, test_client):
        """Health endpoints are public — no Authorization header needed."""
        for path in ["/health", "/health/live", "/health/ready"]:
            response = test_client.get(path)
            assert response.status_code != 401, f"{path} should not require auth"
