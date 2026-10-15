"""
services/unit_test_service.py
-----------------------------
ABAP Unit Automated Regression Testing & Quality Gate Service.
Executes test runs via ADT (/sap/bc/adt/abapunit/testruns) and evaluates regression risk.
"""

from __future__ import annotations

import re
from typing import Any, Dict
from config.settings import settings
from core.logger import logger
from core.state import state
from services.adt_client import adt_client


class UnitTestService:
    """Enterprise ABAP Unit regression testing gate."""

    async def run_abap_unit_tests(self, program_name: str) -> Dict[str, Any]:
        """Runs ABAP Unit test suites for the given program."""
        clean_prog = re.sub(r"[^A-Za-z0-9_/]", "", program_name).strip().upper()
        state.increment_metric("unit_tests_run")

        if settings.sap_mock_mode:
            has_failures = any(term in clean_prog for term in ["FAIL", "REGRESS", "BUG"])
            return {
                "program_name": clean_prog,
                "mock_mode": True,
                "status": "FAILED" if has_failures else "SUCCESS",
                "tests_run": 4,
                "passed": 2 if has_failures else 4,
                "failed": 2 if has_failures else 0,
                "errors": 0,
                "details": [
                    {"test_class": "LCL_TEST_SUITE", "method": "test_normal_flow", "status": "PASSED"},
                    {
                        "test_class": "LCL_TEST_SUITE",
                        "method": "test_edge_cases",
                        "status": "FAILED" if has_failures else "PASSED",
                        "failure_detail": "Assertion failed: expected result <> 0" if has_failures else None,
                    },
                ],
                "message": (
                    "ABAP Unit test regression detected: 2 test(s) failed."
                    if has_failures
                    else "All 4 ABAP Unit test(s) passed successfully."
                ),
            }

        payload = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<aunit:runConfiguration xmlns:aunit="http://www.sap.com/adt/abapunit">\n'
            '  <external>\n'
            '    <coverage active="false"/>\n'
            '  </external>\n'
            '  <adtcore:objectSets xmlns:adtcore="http://www.sap.com/adt/core">\n'
            '    <objectSet>\n'
            '      <adtcore:objectReferences>\n'
            f'        <adtcore:objectReference adtcore:uri="/sap/bc/adt/programs/programs/{clean_prog.lower()}" adtcore:name="{clean_prog}"/>\n'
            '      </adtcore:objectReferences>\n'
            '    </objectSet>\n'
            '  </adtcore:objectSets>\n'
            '</aunit:runConfiguration>'
        )

        try:
            resp = await adt_client.sap_post(
                "/sap/bc/adt/abapunit/testruns",
                content=payload,
                content_type="application/vnd.sap.adt.abapunit.testruns.v1+xml",
            )
            return {
                "program_name": clean_prog,
                "status": "SUCCESS",
                "mock_mode": False,
                "raw_response": resp.text,
                "message": f"ABAP Unit run completed for '{clean_prog}'.",
            }
        except Exception as e:
            return {"program_name": clean_prog, "status": "ERROR", "error": True, "message": str(e)}


unit_test_service = UnitTestService()
