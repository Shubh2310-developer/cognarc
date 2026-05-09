"""
COGNARC — Supabase Adapter
apps/api/app/adapters/supabase_adapter.py

T2.5: Wraps Supabase client with retry/timeout.
§07: External API clients live in adapters/. Retry + timeout enforced.
§16: No secrets in source. Keys from settings only.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logger import get_logger

_logger = get_logger("adapter.supabase")

# Retry config: 3 attempts, exponential backoff 0.5s–4s
_RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=0.5, min=0.5, max=4),
    "reraise": True,
}


class SupabaseAdapter:
    """
    Thin wrapper around the Supabase Auth REST API.
    Handles retry, timeout, and error normalization.

    MVP scope: magic link send + token refresh only.
    Phase 2+: Add OAuth, user management endpoints.
    """

    def __init__(self) -> None:
        self._base_url = f"{settings.SUPABASE_URL}/auth/v1"
        self._headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        }
        self._service_headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

    @retry(**_RETRY_CONFIG)
    async def send_magic_link(self, email: str) -> None:
        """
        Send a Supabase OTP magic link email.
        Uses anon key — public endpoint.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._base_url}/otp",
                headers=self._headers,
                json={"email": email, "create_user": True},
            )
            if response.status_code not in (200, 201):
                _logger.error(
                    "Supabase magic link failed",
                    context={"status": response.status_code, "body": response.text[:200]},
                )
                response.raise_for_status()

    @retry(**_RETRY_CONFIG)
    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Exchange a refresh token for a new access token.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._base_url}/token?grant_type=refresh_token",
                headers=self._headers,
                json={"refresh_token": refresh_token},
            )
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()


@lru_cache(maxsize=1)
def get_supabase_adapter() -> SupabaseAdapter:
    """Return cached SupabaseAdapter singleton."""
    return SupabaseAdapter()
