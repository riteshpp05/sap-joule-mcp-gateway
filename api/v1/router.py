"""
api/v1/router.py
----------------
Composite API router mounting all domain endpoints under /api/v1 and /api.
"""

from __future__ import annotations

from fastapi import APIRouter
from api.v1.endpoints import ai, cds, cts, health, st22, unit_test, chat

api_v1_router = APIRouter()

# Mount all endpoint routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(st22.router)
api_v1_router.include_router(cds.router)
api_v1_router.include_router(cts.router)
api_v1_router.include_router(unit_test.router)
api_v1_router.include_router(ai.router)
api_v1_router.include_router(chat.router)
