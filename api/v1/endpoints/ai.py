"""
api/v1/endpoints/ai.py
----------------------
SAP Joule AI Intelligence Endpoints (Summarization, Modernization, and Natural Language Modeling).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.ai_service import ai_service

router = APIRouter(tags=["AI Intelligence & Joule Copilot"])


class CdsFromEnglishRequest(BaseModel):
    prompt_text: Optional[str] = Field(default=None, description="Natural language specification")
    prompt: Optional[str] = Field(default=None, description="Alias for prompt_text")
    push_to_sap: bool = Field(default=False, description="Deploy live via ADT")
    package: str = Field(default="$TMP", description="Target SAP package")
    transport_request: Optional[str] = Field(default=None, description="CTS Transport Request")
    expose_to_fiori: bool = Field(default=True, description="Add OData publish annotation")


class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., description="ABAP source code snippet")


class CdsDiagnosisRequest(BaseModel):
    raw_error: Optional[str] = Field(default=None, description="Raw checkrun error message")
    error: Optional[str] = Field(default=None, description="Alias for raw_error")


@router.post("/cds/generate_from_english")
@router.post("/generate_from_english")
@router.post("/cds_from_english")
@router.post("/ai/cds_from_english")
async def generate_cds_from_english(req: CdsFromEnglishRequest) -> Dict[str, Any]:
    """Generates structured CDS specification and compiles DDL from plain English description."""
    from services.cds_service import cds_service
    prompt = req.prompt_text or req.prompt or ""
    result = await ai_service.generate_cds_from_english(prompt)
    if "error" in result:
        return result

    return await cds_service.create_cds_view(
        view_name=result.get("view_name", "Z_I_CustomView"),
        table_name=result.get("table_name", "vbak"),
        fields=result.get("fields", []),
        joins=result.get("joins", []),
        associations=result.get("associations", []),
        view_type=result.get("view_type", "entity"),
        expose_to_fiori=req.expose_to_fiori,
        push_to_sap=req.push_to_sap,
        package=req.package,
        transport_request=req.transport_request,
    )


@router.post("/abap/summary")
@router.post("/summary")
@router.post("/summarize_abap")
@router.post("/ai/summarize_abap")
async def summarize_abap(req: CodeAnalysisRequest) -> Dict[str, str]:
    """Summarizes ABAP code architecture and business logic."""
    summary = await ai_service.summarize_abap_logic(req.code)
    return {"summary": summary}


@router.post("/abap/optimize")
@router.post("/optimize")
@router.post("/optimize_abap")
@router.post("/ai/optimize_abap")
async def optimize_abap(req: CodeAnalysisRequest) -> Dict[str, str]:
    """Analyzes ABAP code and suggests Clean ABAP 7.40+ optimizations."""
    optimization = await ai_service.optimize_abap_code(req.code)
    return {"optimization": optimization}


@router.post("/cds/explain_diagnosis")
@router.post("/explain_diagnosis")
@router.post("/explain_cds_diagnosis")
@router.post("/ai/explain_cds_diagnosis")
async def explain_cds_diagnosis(req: CdsDiagnosisRequest) -> Dict[str, str]:
    """Explains CDS checkrun activation errors with actionable steps."""
    err_text = req.raw_error or req.error or ""
    diagnosis = await ai_service.explain_cds_diagnosis(err_text)
    return {"explanation": diagnosis, "diagnosis": diagnosis}
