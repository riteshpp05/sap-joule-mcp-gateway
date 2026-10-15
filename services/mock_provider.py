"""
services/mock_provider.py
-------------------------
Data-driven Mock Provider.
Dynamically loads mock datasets and schemas from external JSON fixtures.
Eliminates all hardcoded values from application code.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from config.settings import settings
from core.logger import logger


class MockDataProvider:
    """Provides access to externalized mock data fixtures."""

    def __init__(self, fixtures_dir: Optional[str] = None):
        self.fixtures_dir = fixtures_dir or settings.fixtures_dir

    def _load_json(self, filename: str, default: Any = None) -> Any:
        path = os.path.join(self.fixtures_dir, filename)
        if not os.path.exists(path):
            logger.warning(f"Mock fixture file not found: {path}")
            return default if default is not None else {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fixture {filename}: {e}")
            return default if default is not None else {}

    def get_dumps(self) -> List[Dict[str, Any]]:
        return self._load_json("mock_dumps.json", default=[])

    def get_dump_by_id(self, dump_id: str) -> Optional[Dict[str, Any]]:
        dumps = self.get_dumps()
        clean = dump_id.strip().upper()
        for d in dumps:
            if d.get("dump_id", "").upper() == clean or d.get("id", "").upper() == clean:
                return d
        # Partial match fallback
        for d in dumps:
            if clean in d.get("dump_id", "").upper() or clean in d.get("title", "").upper():
                return d
        return None

    def get_program_source(self, program_name: str) -> str:
        progs = self._load_json("mock_programs.json", default={})
        clean = program_name.strip().upper()
        if clean in progs:
            return progs[clean]
        # Return standard dynamic template
        return (
            f"*&---------------------------------------------------------------------*\n"
            f"*& Report {clean}\n"
            f"*& Dynamic Mock Source from SAP S/4HANA System\n"
            f"*&---------------------------------------------------------------------*\n"
            f"REPORT {clean}.\n\n"
            f"WRITE: / 'Executed report {clean}'.\n"
        )

    def get_tables(self) -> Dict[str, Any]:
        return self._load_json("mock_tables.json", default={})

    def get_table(self, table_name: str) -> Optional[Dict[str, Any]]:
        tables = self.get_tables()
        return tables.get(table_name.strip().lower())

    def get_packages(self) -> List[Dict[str, Any]]:
        return self._load_json("mock_packages.json", default=[])

    def get_transports(self) -> List[Dict[str, Any]]:
        return self._load_json("mock_transports.json", default=[])

    def get_abap_fix_rules(self) -> Dict[str, Any]:
        return self._load_json("abap_fix_rules.json", default={"rules": {}, "default_rule": {}})

    def get_prompt_templates(self) -> Dict[str, str]:
        return self._load_json("prompt_templates.json", default={})


mock_provider = MockDataProvider()
