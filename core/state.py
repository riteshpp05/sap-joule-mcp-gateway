"""
core/state.py
-------------
Thread-safe in-memory state management, audit logs, and metrics for the SAP Joule Gateway.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class AppState:
    """Thread-safe state manager for application metrics, audit trails, and proposals."""

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: Dict[str, int] = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "rollbacks_total": 0,
            "unit_tests_run": 0,
            "proposals_generated": 0,
            "proposals_pushed": 0,
        }
        self._audit_logs: List[Dict[str, Any]] = []
        self._fix_proposals: Dict[str, Dict[str, Any]] = {}
        self._start_time = time.time()

    def increment_metric(self, key: str, amount: int = 1) -> None:
        with self._lock:
            self._metrics[key] = self._metrics.get(key, 0) + amount

    def get_metrics(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._metrics)

    def record_audit(self, event_type: str, details: Dict[str, Any], correlation_id: str = "-") -> None:
        entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            "correlation_id": correlation_id,
            "details": details,
        }
        with self._lock:
            self._audit_logs.append(entry)
            # Retain only last 500 audit logs to prevent memory leak
            if len(self._audit_logs) > 500:
                self._audit_logs.pop(0)

    def get_recent_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._audit_logs[-limit:])

    def save_proposal(self, dump_id: str, proposal_data: Dict[str, Any]) -> None:
        with self._lock:
            self._fix_proposals[dump_id] = proposal_data
            self._metrics["proposals_generated"] += 1

    def get_proposal(self, dump_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._fix_proposals.get(dump_id)

    def get_uptime_seconds(self) -> float:
        return time.time() - self._start_time


state = AppState()
