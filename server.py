"""
server.py
---------
Production-Grade Unified Dual-Mode Gateway & Server for SAP Joule AI Agent.
Coordinates REST API v1, MCP (Streamable-HTTP & SSE), and modern React Studio.
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.v1.router import api_v1_router
from config.settings import settings
from config.constants import HEADER_CORRELATION_ID, HEADER_REQUEST_ID, HEADER_RESPONSE_TIME
from core.exceptions import GatewayBaseException, gateway_exception_handler
from core.logger import logger
from core.state import state
from mcp_server.fastmcp_app import mcp, mcp_sh_app, mcp_sse_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bridges FastMCP sub-application lifespans with parent FastAPI app."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} on {settings.host}:{settings.port}")
    async with mcp_sh_app.lifespan(app), mcp_sse_app.lifespan(app):
        yield
    logger.info("Gateway shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    description="Production-Grade SAP Joule AI Agent & MCP Gateway with S/4HANA ADT Integration.",
    version=settings.app_version,
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(GatewayBaseException, gateway_exception_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_and_correlation_middleware(request: Request, call_next):
    corr_id = request.headers.get(HEADER_CORRELATION_ID) or request.headers.get(HEADER_REQUEST_ID) or str(uuid.uuid4())
    request.state.correlation_id = corr_id
    start_time = time.time()
    state.increment_metric("requests_total")

    # Path normalization for MCP sub-apps
    if request.scope["path"] == "/mcp":
        request.scope["path"] = "/mcp/"
    elif request.scope["path"] == "/sse":
        request.scope["path"] = "/sse/"

    # Optional Enterprise API Key Protection
    configured_key = settings.gateway_api_key.strip()
    if (
        configured_key
        and not request.url.path.startswith(("/health", "/metrics", "/static", "/assets"))
        and request.url.path not in ("/", "/legacy", "/docs", "/openapi.json")
    ):
        api_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization", "")
        bearer_token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
        if api_key != configured_key and bearer_token != configured_key:
            state.increment_metric("requests_error")
            return JSONResponse(
                status_code=401,
                content={"error": True, "message": "Unauthorized: Invalid or missing API Key/Bearer token."},
                headers={HEADER_CORRELATION_ID: corr_id},
            )

    try:
        response = await call_next(request)
        duration = time.time() - start_time
        response.headers[HEADER_CORRELATION_ID] = corr_id
        response.headers[HEADER_RESPONSE_TIME] = f"{duration:.4f}s"
        if response.status_code >= 400:
            state.increment_metric("requests_error")
        else:
            state.increment_metric("requests_success")
        return response
    except Exception as exc:
        state.increment_metric("requests_error")
        logger.error(f"[{corr_id}] Request to {request.url.path} failed: {exc}")
        raise exc


# Mount MCP Sub-Apps
app.mount("/mcp", mcp_sh_app)
app.mount("/sse", mcp_sse_app)

# Mount Routers (Dual registration for backward compatibility with root /api and /api/v1)
app.include_router(api_v1_router)
app.include_router(api_v1_router, prefix="/api")
app.include_router(api_v1_router, prefix="/api/v1")

# Mount Static Assets & UI
react_static_dir = os.path.join(os.path.dirname(__file__), "static_react")
legacy_static_dir = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(react_static_dir):
    react_assets_dir = os.path.join(react_static_dir, "assets")
    if os.path.exists(react_assets_dir):
        app.mount("/assets", StaticFiles(directory=react_assets_dir), name="assets")

if os.path.exists(legacy_static_dir):
    app.mount("/static", StaticFiles(directory=legacy_static_dir), name="static")


@app.get("/", response_class=FileResponse)
async def read_index():
    react_index = os.path.join(react_static_dir, "index.html")
    if os.path.exists(react_index):
        return FileResponse(react_index)
    legacy_index = os.path.join(legacy_static_dir, "index.html")
    if os.path.exists(legacy_index):
        return FileResponse(legacy_index)
    return {"message": f"{settings.app_name} is running. Frontend static build pending."}


@app.get("/legacy", response_class=FileResponse)
async def read_legacy_index():
    legacy_index = os.path.join(legacy_static_dir, "index.html")
    if os.path.exists(legacy_index):
        return FileResponse(legacy_index)
    return {"message": "Legacy UI not found."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=settings.debug)
