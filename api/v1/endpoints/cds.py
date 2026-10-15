"""
api/v1/endpoints/cds.py
-----------------------
Core Data Services (CDS) Studio, Checkrun Diagnosis, and DDL Deployment Endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.cds_service import cds_service

router = APIRouter(tags=["CDS View Entity Studio"])


class CreateCdsRequest(BaseModel):
    view_name: str = Field(..., description="Target CDS View Name")
    table_name: str = Field(..., description="Primary DB table or entity")
    fields: List[str] = Field(..., description="Selected fields with keys and aliases")
    joins: Optional[List[Dict[str, str]]] = Field(default=None, description="JOIN specifications")
    associations: Optional[List[Dict[str, str]]] = Field(default=None, description="Association specifications")
    sql_view_name: Optional[str] = Field(default=None, description="16-character SQL view name for classic views")
    view_type: str = Field(default="classic", description="'entity' or 'classic'")
    expose_to_fiori: bool = Field(default=True, description="Add @OData.publish: true")
    push_to_sap: bool = Field(default=False, description="Deploy live via ADT")
    package: str = Field(default="$TMP", description="Target SAP Package")
    create_package_if_missing: bool = Field(default=False, description="Auto-create package if not found")
    transport_request: Optional[str] = Field(default=None, description="CTS Transport Request")


class DiagnoseCdsRequest(BaseModel):
    view_name: str = Field(..., description="CDS View to diagnose")


class PushCdsRequest(BaseModel):
    view_name: str = Field(..., description="CDS View Name")
    ddl: str = Field(..., description="Approved DDL source code")
    package: str = Field(default="$TMP", description="Target SAP Package")
    transport_request: Optional[str] = Field(default=None, description="CTS Transport Request")


@router.post("/create")
@router.post("/cds/create")
async def create_cds(req: CreateCdsRequest) -> Dict[str, Any]:
    """Compiles CDS view DDL and optionally deploys to SAP."""
    return await cds_service.create_cds_view(
        view_name=req.view_name,
        table_name=req.table_name,
        fields=req.fields,
        joins=req.joins,
        associations=req.associations,
        sql_view_name=req.sql_view_name,
        view_type=req.view_type,
        expose_to_fiori=req.expose_to_fiori,
        push_to_sap=req.push_to_sap,
        package=req.package,
        create_package_if_missing=req.create_package_if_missing,
        transport_request=req.transport_request,
    )


@router.post("/diagnose")
@router.post("/cds/diagnose")
async def diagnose_cds(req: DiagnoseCdsRequest) -> Dict[str, Any]:
    """Executes checkrun syntax diagnostics on a CDS view."""
    return await cds_service.diagnose_cds_issue(req.view_name)


@router.post("/repair")
@router.post("/cds/repair")
@router.post("/autofix")
@router.post("/cds/autofix")
async def repair_cds(req: DiagnoseCdsRequest) -> Dict[str, Any]:
    """Automatically repairs common syntax errors in CDS DDL."""
    return await cds_service.auto_fix_cds_view(req.view_name)


@router.post("/push_fix")
@router.post("/cds/push_fix")
async def push_cds_fix(req: PushCdsRequest) -> Dict[str, Any]:
    """Pushes approved DDL live to SAP ADT."""
    return await cds_service.push_cds_view_to_sap(
        view_name=req.view_name,
        ddl=req.ddl,
        package=req.package,
        transport_request=req.transport_request,
    )
