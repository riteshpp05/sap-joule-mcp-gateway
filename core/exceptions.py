"""
core/exceptions.py
------------------
Standardized RFC 7807 problem details and domain exceptions for the SAP Joule Gateway.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse


class GatewayBaseException(Exception):
    """Base domain exception for SAP Joule Gateway."""

    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class LockConflictError(GatewayBaseException):
    """Raised when an SAP ADT object is locked by another user or session (HTTP 409/423)."""

    def __init__(self, message: str, locked_by: str = "UNKNOWN_USER"):
        super().__init__(message, status_code=409, details={"locked_by": locked_by})
        self.locked_by = locked_by


class SAPActivationError(GatewayBaseException):
    """Raised when an SAP object fails syntax check or ADT activation."""

    def __init__(self, message: str, syntax_errors: Optional[list] = None):
        super().__init__(message, status_code=422, details={"syntax_errors": syntax_errors or []})
        self.syntax_errors = syntax_errors or []


class GovernancePolicyError(GatewayBaseException):
    """Raised when CTS governance or security checks fail."""

    def __init__(self, message: str):
        super().__init__(message, status_code=403)


async def gateway_exception_handler(request: Request, exc: GatewayBaseException) -> JSONResponse:
    """Formats GatewayBaseException into RFC 7807 compliant Problem Details."""
    corr_id = getattr(request.state, "correlation_id", "-")
    content = {
        "type": f"https://sap-joule-gateway.internal/errors/{exc.__class__.__name__}",
        "title": exc.__class__.__name__,
        "status": exc.status_code,
        "detail": exc.message,
        "instance": request.url.path,
        "correlation_id": corr_id,
        **exc.details,
    }
    return JSONResponse(status_code=exc.status_code, content=content)
