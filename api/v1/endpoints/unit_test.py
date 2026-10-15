"""
api/v1/endpoints/unit_test.py
-----------------------------
ABAP Unit Automated Regression Testing Quality Gate Endpoint.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.unit_test_service import unit_test_service

router = APIRouter(tags=["ABAP Unit Testing"])


class UnitTestRequest(BaseModel):
    program_name: str = Field(..., description="Target ABAP Program Name")


@router.post("/unit_tests")
@router.post("/abap/unit_tests")
async def run_unit_tests(req: UnitTestRequest) -> Dict[str, Any]:
    """Executes ABAP Unit test suite to verify regression status."""
    return await unit_test_service.run_abap_unit_tests(req.program_name)
