"""
api/v1/endpoints/health.py
--------------------------
Health probes, Kubernetes liveness/readiness, and Prometheus telemetry endpoints.
"""

from __future__ import annotations

import time
from typing import Any, Dict
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from config.settings import settings
from core.state import state

router = APIRouter(tags=["Observability & Health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Base health check returning system readiness and gateway modes."""
    return {
        "status": "ok",
        "modes": ["rest:/api/*", "mcp:/mcp (streamable-http)", "mcp:/sse (sse)"],
        "timestamp": time.time(),
        "uptime_seconds": round(state.get_uptime_seconds(), 2),
        "app_name": settings.app_name,
        "app_version": settings.app_version,
    }


@router.get("/health/live")
async def liveness_probe() -> Dict[str, Any]:
    """Kubernetes/Cloud Foundry Liveness probe verifying server event-loop responsiveness."""
    return {
        "status": "ALIVE",
        "timestamp": time.time(),
        "uptime_seconds": round(state.get_uptime_seconds(), 2),
        "app_name": settings.app_name,
        "app_version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """Readiness probe checking SAP backend connectivity / mock state."""
    return {
        "status": "READY",
        "sap_base_url": settings.sap_base_url,
        "sap_client": settings.sap_client,
        "mock_mode": settings.sap_mock_mode,
        "mcp_enabled": True,
        "version": settings.app_version,
    }


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics() -> str:
    """Prometheus exposition metrics."""
    m = state.get_metrics()
    uptime = state.get_uptime_seconds()
    lines = [
        "# HELP gateway_requests_total Total number of HTTP requests processed.",
        "# TYPE gateway_requests_total counter",
        f"gateway_requests_total {m.get('requests_total', 0)}",
        "# HELP gateway_requests_success Total successful HTTP requests.",
        "# TYPE gateway_requests_success counter",
        f"gateway_requests_success {m.get('requests_success', 0)}",
        "# HELP gateway_requests_error Total failed HTTP requests.",
        "# TYPE gateway_requests_error counter",
        f"gateway_requests_error {m.get('requests_error', 0)}",
        "# HELP sap_rollbacks_total Total automated rollback events triggered.",
        "# TYPE sap_rollbacks_total counter",
        f"sap_rollbacks_total {m.get('rollbacks_total', 0)}",
        f"gateway_rollbacks_total {m.get('rollbacks_total', 0)}",
        "# HELP gateway_unit_tests_run Total ABAP Unit test runs executed.",
        "# TYPE gateway_unit_tests_run counter",
        f"gateway_unit_tests_run {m.get('unit_tests_run', 0)}",
        "# HELP gateway_uptime_seconds Uptime of the gateway process in seconds.",
        "# TYPE gateway_uptime_seconds gauge",
        f"gateway_uptime_seconds {uptime:.2f}",
    ]
    return "\n".join(lines) + "\n"


@router.get("/api/v1/audit/logs")
async def get_audit_logs(limit: int = 50) -> Dict[str, Any]:
    """Retrieves recent enterprise audit trails."""
    logs = state.get_recent_audit_logs(limit=limit)
    return {"count": len(logs), "logs": logs}
