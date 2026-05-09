"""
COGNARC — API v1 Router
apps/api/app/api/v1/router.py

Aggregates all v1 sub-routers. Each module owns its routes per §06.
Health routes are registered directly on app (no /api/v1 prefix) in main.py.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

# Future Phase 1 routes (imported as they are implemented):
# from app.api.v1.quests import router as quests_router
# from app.api.v1.gamification import router as gamification_router
# from app.api.v1.skills import router as skills_router

api_router = APIRouter()

# Register sub-routers with prefixes per §06 route table
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
