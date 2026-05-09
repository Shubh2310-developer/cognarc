"""
COGNARC — Root conftest.py
apps/api/conftest.py

Root-level pytest configuration that runs before any test collection.
Adds ai-services to sys.path so tests can import ai_services.* modules.

§07: ai-services is isolated but tests must be able to import it directly
     to test parsing, validation, and adapter logic in isolation.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Path Setup ────────────────────────────────────────────────
# Add ai-services to Python path so unit tests can import ai_services.*
_REPO_ROOT = Path(__file__).parent.parent.parent  # cognarc/
_AI_SERVICES_DIR = _REPO_ROOT / "ai-services"

if str(_AI_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_SERVICES_DIR))

# ── Test Environment ──────────────────────────────────────────
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("MONGODB_URL", "")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret-key-for-testing-only-32chars")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
