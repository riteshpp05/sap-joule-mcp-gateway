"""
core/security.py
----------------
Authentication and authorization guard for the SAP Joule Gateway.
Provides Bearer token and X-API-Key verification via FastAPI dependencies.
"""

from __future__ import annotations

from typing import Optional
from fastapi import Header, HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader
from config.settings import settings
from config.constants import HEADER_API_KEY
from core.state import state

api_key_header = APIKeyHeader(name=HEADER_API_KEY, auto_error=False)


async def verify_gateway_auth(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    authorization: Optional[str] = Header(default=None),
) -> bool:
    """Verifies gateway authentication if GATEWAY_API_KEY is configured in settings.
    If no key is configured, access is unrestricted.
    """
    configured_key = settings.gateway_api_key.strip()
    if not configured_key:
        return True

    # Check X-API-Key header
    if api_key and api_key.strip() == configured_key:
        return True

    # Check Authorization: Bearer <token>
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == configured_key:
            return True

    state.increment_metric("requests_error")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Missing or invalid Gateway API Key / Bearer token.",
    )
