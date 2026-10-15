"""
api/v1/endpoints/st22.py
------------------------
ST22 Short Dump Triage, Auto-Fix Proposal, and Safe ABAP Push Endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from services.st22_service import st22_service

router = APIRouter(tags=["ST22 Short Dumps & ABAP Fix"])


class DumpDetailRequest(BaseModel):
    dump_id: str = Field(..., description="SAP Short Dump ID or fragment")


class AutoFixRequest(BaseModel):
    dump_id: str = Field(..., description="SAP Short Dump ID to remediate")


class PushFixRequest(BaseModel):
    program_name: str = Field(..., description="Target ABAP Program Name")
    fixed_code: str = Field(..., description="Remediated ABAP code")
    dump_id: Optional[str] = Field(default=None, description="Associated short dump ID")
    confirm_push: bool = Field(default=False, description="Explicit approval gate")
    package: str = Field(default="$TMP", description="Target SAP DevClass")
    transport_request: Optional[str] = Field(default=None, description="CTS Transport Request")
    run_unit_tests: bool = Field(default=True, description="Execute ABAP Unit regression check")
    auto_rollback_on_test_failure: bool = Field(default=True, description="Rollback on test regression")


@router.get("/dumps")
@router.get("/abap/dumps")
async def list_dumps(max_results: int = Query(default=20, ge=1, le=100)) -> Dict[str, Any]:
    """Retrieves recent ST22 short dumps."""
    return await st22_service.list_recent_dumps(max_results=max_results)


@router.post("/st22")
@router.post("/abap/st22")
async def analyze_dump(req: DumpDetailRequest) -> Dict[str, Any]:
    """Retrieves detailed ST22 XML analysis for a dump ID."""
    return await st22_service.analyze_st22_dump(req.dump_id)


@router.post("/auto_fix")
@router.post("/abap/auto_fix")
async def propose_auto_fix(req: AutoFixRequest) -> Dict[str, Any]:
    """Synthesizes an auto-fix proposal for human review."""
    return await st22_service.auto_fix_abap(req.dump_id)


@router.post("/push_fix")
@router.post("/abap/push_fix")
async def push_fix(req: PushFixRequest) -> Dict[str, Any]:
    """Pushes an approved fix to SAP ADT with lock conflict and rollback protection."""
    return await st22_service.push_abap_fix(
        program_name=req.program_name,
        fixed_code=req.fixed_code,
        dump_id=req.dump_id,
        confirm_push=req.confirm_push,
        package=req.package,
        transport_request=req.transport_request,
        run_unit_tests=req.run_unit_tests,
        auto_rollback_on_test_failure=req.auto_rollback_on_test_failure,
    )


@router.get("/abap/source/{program}")
async def get_abap_source(program: str) -> Dict[str, Any]:
    """Fetches ABAP source code for a program."""
    return await st22_service.fetch_abap_source(program)
