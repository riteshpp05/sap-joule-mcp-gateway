"""
api/v1/endpoints/cts.py
-----------------------
Enterprise CTS Transport Request Governance & DevClass Management Endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.cts_service import cts_service

router = APIRouter(tags=["CTS Transport Governance & Packages"])


class ValidateTransportRequest(BaseModel):
    package: str = Field(..., description="Target SAP Package")
    transport_request: Optional[str] = Field(default=None, description="CTS Transport Request")


class CreatePackageRequest(BaseModel):
    package_name: str = Field(..., description="SAP DevClass name")
    description: Optional[str] = Field(default=None, description="Package description")
    software_component: str = Field(default="HOME", description="Software component")
    transport_layer: str = Field(default="SAP", description="Transport layer")
    super_package: Optional[str] = Field(default=None, description="Super package")
    transport_request: Optional[str] = Field(default=None, description="Transport request")
    push_to_sap: bool = Field(default=True, description="Deploy live to SAP")


@router.post("/validate")
@router.post("/cts/validate")
async def validate_transport(req: ValidateTransportRequest) -> Dict[str, Any]:
    """Validates transport request compliance according to SAP CTS conventions."""
    return cts_service.validate_transport_request(
        transport_request=req.transport_request,
        package=req.package,
    )


@router.post("/package")
@router.post("/abap/package")
@router.post("/package/create")
async def create_package(req: CreatePackageRequest) -> Dict[str, Any]:
    """Creates a new SAP development package via ADT."""
    return await cts_service.create_sap_package(
        package_name=req.package_name,
        description=req.description,
        software_component=req.software_component,
        transport_layer=req.transport_layer,
        super_package=req.super_package,
        transport_request=req.transport_request,
        push_to_sap=req.push_to_sap,
    )
