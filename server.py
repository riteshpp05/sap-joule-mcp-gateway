"""
server.py
---------
Unified Dual-Mode Gateway & Server for the SAP ABAP & CDS Agent.

Architecture:
  1. REST Interface -> /api/* (OpenAPI 3.0 endpoints consumed by SAP Joule / Build Actions)
  2. MCP Interface  -> /mcp   (FastMCP Streamable-HTTP transport for Model Context Protocol clients)
  3. Web Studio     -> /      (Fiori Horizon clean developer workbench)

Technical Notes:
  - FastMCP Streamable-HTTP transport is exposed on /mcp.
  - The FastMCP lifespan is explicitly bridged to FastAPI's parent lifespan to guarantee
    clean initialization and graceful teardown of async task groups.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from fastmcp import FastMCP

import abap_client
import ai_engine

# ---------------------------------------------------------------------------
# 1. FastMCP Server Definition & Tool Registration
# ---------------------------------------------------------------------------

mcp = FastMCP("abap_cds_debug_agent")


@mcp.tool()
async def fetch_abap_source(program: str) -> dict:
    """Fetch ABAP source code for a given program name."""
    return await abap_client.fetch_abap_source(program)


@mcp.tool()
async def analyze_st22_dump(dump_id: str) -> dict:
    """Analyze an ST22 short dump by dump ID."""
    return await abap_client.analyze_st22_dump(dump_id)


@mcp.tool()
async def list_recent_dumps(max_results: int = 20) -> dict:
    """List recent ST22 short dumps from SAP with their real dump_id values
    (use this first if you don't know the exact dump_id to pass to
    analyze_st22_dump / auto_fix_abap)."""
    return await abap_client.list_recent_dumps(max_results)


@mcp.tool()
async def auto_fix_abap(dump_id: str) -> dict:
    """Propose an auto-fix for an ABAP short dump. Returns a proposal for user review
    before pushing live to SAP using push_abap_fix."""
    return await abap_client.auto_fix_abap(dump_id)


@mcp.tool()
async def push_abap_fix(
    program_name: str,
    fixed_code: str,
    dump_id: str | None = None,
    confirm_push: bool = False,
    package: str = "$TMP",
    transport_request: str | None = None,
) -> dict:
    """Push an approved ABAP auto-fix live to the SAP system via ADT.
    Requires user controller confirmation (confirm_push=True)."""
    return await abap_client.push_abap_fix(
        program_name=program_name,
        fixed_code=fixed_code,
        dump_id=dump_id,
        confirm_push=confirm_push,
        package=package,
        transport_request=transport_request,
    )


@mcp.tool()
async def create_sap_package(
    package_name: str,
    description: str | None = None,
    software_component: str = "HOME",
    transport_layer: str = "SAP",
    super_package: str | None = None,
    transport_request: str | None = None,
    push_to_sap: bool = True,
) -> dict:
    """Create a new SAP Development Package (DevClass) live in the SAP system via ADT."""
    return await abap_client.create_sap_package(
        package_name=package_name,
        description=description,
        software_component=software_component,
        transport_layer=transport_layer,
        super_package=super_package,
        transport_request=transport_request,
        push_to_sap=push_to_sap,
    )


@mcp.tool()
async def create_cds_view(
    view_name: str,
    table_name: str,
    fields: list[str],
    joins: list[dict[str, str]] | None = None,
    associations: list[dict[str, str]] | None = None,
    sql_view_name: str | None = None,
    expose_to_fiori: bool = True,
    push_to_sap: bool = False,
    package: str = "$TMP",
    create_package_if_missing: bool = False,
    transport_request: str | None = None,
) -> dict:
    """Generate a new CDS view DDL definition supporting single and multiple tables (JOINs & Associations).
    Set push_to_sap=True to also create and activate it live in the SAP system.
    Set create_package_if_missing=True to auto-create the target package if needed."""
    return await abap_client.create_cds_view(
        view_name=view_name,
        table_name=table_name,
        fields=fields,
        joins=joins,
        associations=associations,
        sql_view_name=sql_view_name,
        expose_to_fiori=expose_to_fiori,
        push_to_sap=push_to_sap,
        package=package,
        create_package_if_missing=create_package_if_missing,
        transport_request=transport_request,
    )


@mcp.tool()
async def diagnose_cds_issue(view_name: str) -> dict:
    """Diagnose why a CDS view failed to activate."""
    return await abap_client.diagnose_cds_issue(view_name)


@mcp.tool()
async def auto_fix_cds_view(view_name: str) -> dict:
    """Attempt to auto-repair a broken CDS view."""
    return await abap_client.auto_fix_cds_view(view_name)


@mcp.tool()
async def push_cds_fix(
    view_name: str,
    ddl: str,
    package: str = "$TMP",
    transport_request: str | None = None,
) -> dict:
    """Push an approved repaired CDS view live to the SAP system via ADT."""
    return await abap_client.push_cds_view_to_sap(
        view_name=view_name,
        ddl=ddl,
        package=package,
        transport_request=transport_request,
    )


@mcp.tool()
async def summarize_abap_logic(code: str) -> dict:
    """Summarize the logic and architecture of an ABAP program in plain English."""
    summary = await ai_engine.summarize_abap_logic(code)
    return {"summary": summary}


@mcp.tool()
async def optimize_abap_code(code: str) -> dict:
    """Analyze ABAP code and suggest 7.40+ modern syntax expressions and performance optimizations."""
    optimization = await ai_engine.optimize_abap_code(code)
    return {"optimization": optimization}


@mcp.tool()
async def explain_cds_diagnosis(raw_error: str) -> dict:
    """Explain an SAP CDS View activation error with actionable step-by-step remediation advice."""
    explanation = await ai_engine.explain_cds_diagnosis(raw_error)
    return {"explanation": explanation}


@mcp.tool()
async def generate_cds_from_english(
    prompt_text: str,
    package: str = "$TMP",
    transport_request: str | None = None,
    expose_to_fiori: bool = True,
    push_to_sap: bool = False,
) -> dict:
    """Generate a CDS View definition from an English description and optionally deploy live to SAP."""
    result = await ai_engine.generate_cds_from_english(prompt_text)
    if "error" in result:
        return result
    return await abap_client.create_cds_view(
        view_name=result.get("view_name"),
        table_name=result.get("table_name"),
        fields=result.get("fields", []),
        joins=result.get("joins", []),
        expose_to_fiori=expose_to_fiori,
        push_to_sap=push_to_sap,
        package=package,
        transport_request=transport_request,
    )


# ---------------------------------------------------------------------------
# 2. MCP ASGI apps -- STREAMABLE-HTTP aur SSE transport modes.
# ---------------------------------------------------------------------------

mcp_sh_app = mcp.http_app(path="/", transport="streamable-http")
mcp_sse_app = mcp.http_app(path="/", transport="sse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_sh_app.lifespan(app), mcp_sse_app.lifespan(app):
        yield


# ---------------------------------------------------------------------------
# 3. Parent FastAPI app -- composite lifespan context.
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ABAP & CDS AI Debug Agent API",
    description="REST + MCP dual-mode server for SAP ADT integration.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rewrite_mcp_path(request: Request, call_next):
    if request.scope["path"] == "/mcp":
        request.scope["path"] = "/mcp/"
    elif request.scope["path"] == "/sse":
        request.scope["path"] = "/sse/"
    return await call_next(request)


app.mount("/mcp", mcp_sh_app)
app.mount("/sse", mcp_sse_app)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=FileResponse)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AIS ABAP & CDS AI Debug Studio API is running. UI file not found."}


@app.get("/api/test_debug")
async def test_debug():
    if abap_client.SAP_MOCK_MODE:
        return {
            "status": "MOCK_MODE",
            "mock_mode": True,
            "sap_base_url": abap_client.SAP_BASE_URL,
            "username": abap_client.SAP_USERNAME,
            "message": "SAP_MOCK_MODE is enabled. All external ADT network requests are simulated.",
            "discovery": {"status": 200, "x_csrf_token": "MOCK_CSRF_TOKEN_12345"},
            "paths": {
                "/sap/bc/adt/programs/programs/z_demo1": {
                    "status": 200,
                    "text": "* Mock Demo Program Source\nREPORT z_demo1.\nWRITE: / 'Hello from Simulated SAP ADT Gateway'."
                }
            }
        }

    from btp_proxy import get_sap_client
    import httpx

    sap_base_url = abap_client.SAP_BASE_URL
    username = abap_client.SAP_USERNAME
    password = abap_client.SAP_PASSWORD

    client = await get_sap_client()
    results = {"sap_base_url": sap_base_url, "username": username}
    async with client:
        # Test 1: Discovery
        try:
            r1 = await client.get(f"{sap_base_url}/sap/bc/adt/discovery", auth=(username, password), headers={"X-CSRF-Token": "Fetch"})
            results["discovery"] = {"status": r1.status_code, "x_csrf_token": r1.headers.get("x-csrf-token")}
        except Exception as e:
            results["discovery"] = {"error": str(e)}

        # Test 2: Program source variations
        paths = [
            "/sap/bc/adt/programs/programs/z_demo1",
            "/sap/bc/adt/programs/programs/z_demo1/source/main",
            "/sap/bc/adt/programs/programs/zdemo1/source/main",
            "/sap/bc/adt/programs/programs/rs_abap_source/source/main",
            "/sap/bc/adt/repository/nodestructure",
        ]
        results["paths"] = {}
        for p in paths:
            try:
                rp = await client.get(f"{sap_base_url}{p}", auth=(username, password), headers={"Accept": "*/*"})
                results["paths"][p] = {"status": rp.status_code, "text": rp.text[:300]}
            except httpx.HTTPStatusError as e:
                results["paths"][p] = {"status": e.response.status_code, "text": e.response.text[:300]}
            except Exception as e:
                results["paths"][p] = {"error": str(e)}

    return results



# ---------------------------------------------------------------------------
# 4. REST routes -- openapi.json ke exact paths/operationIds ke sath match.
# ---------------------------------------------------------------------------

class St22Request(BaseModel):
    dump_id: str


class AbapPushFixRequest(BaseModel):
    program_name: str
    fixed_code: str
    dump_id: str | None = None
    confirm_push: bool = False
    package: str = "$TMP"
    transport_request: str | None = None


class PackageCreateRequest(BaseModel):
    package_name: str
    description: str | None = None
    software_component: str = "HOME"
    transport_layer: str = "SAP"
    super_package: str | None = None
    transport_request: str | None = None
    push_to_sap: bool = True


class CdsCreateRequest(BaseModel):
    view_name: str
    table_name: str
    fields: list[str]
    joins: list[dict[str, str]] | None = None
    associations: list[dict[str, str]] | None = None
    sql_view_name: str | None = None
    expose_to_fiori: bool = True
    push_to_sap: bool = False
    package: str = "$TMP"
    create_package_if_missing: bool = False
    transport_request: str | None = None


class CdsViewNameRequest(BaseModel):
    view_name: str


class CdsPushFixRequest(BaseModel):
    view_name: str
    ddl: str
    package: str = "$TMP"
    transport_request: str | None = None


@app.get("/api/abap/source", operation_id="fetch_abap_source")
async def rest_fetch_abap_source(program: str):
    try:
        return await abap_client.fetch_abap_source(program)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/abap/st22", operation_id="analyze_st22_dump")
async def rest_analyze_st22_dump(body: St22Request):
    try:
        return await abap_client.analyze_st22_dump(body.dump_id)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/abap/dumps", operation_id="list_recent_dumps")
async def rest_list_recent_dumps(max_results: int = 20):
    try:
        return await abap_client.list_recent_dumps(max_results)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/abap/autofix", operation_id="auto_fix_abap")
async def rest_auto_fix_abap(body: St22Request):
    try:
        return await abap_client.auto_fix_abap(body.dump_id)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/abap/push_fix", operation_id="push_abap_fix")
async def rest_push_abap_fix(body: AbapPushFixRequest):
    try:
        return await abap_client.push_abap_fix(
            program_name=body.program_name,
            fixed_code=body.fixed_code,
            dump_id=body.dump_id,
            confirm_push=body.confirm_push,
            package=body.package,
            transport_request=body.transport_request,
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/package/create", operation_id="create_sap_package")
async def rest_create_sap_package(body: PackageCreateRequest):
    try:
        return await abap_client.create_sap_package(
            package_name=body.package_name,
            description=body.description,
            software_component=body.software_component,
            transport_layer=body.transport_layer,
            super_package=body.super_package,
            transport_request=body.transport_request,
            push_to_sap=body.push_to_sap,
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/cds/create", operation_id="create_cds_view")
async def rest_create_cds_view(body: CdsCreateRequest):
    try:
        return await abap_client.create_cds_view(
            view_name=body.view_name,
            table_name=body.table_name,
            fields=body.fields,
            joins=body.joins,
            associations=body.associations,
            sql_view_name=body.sql_view_name,
            expose_to_fiori=body.expose_to_fiori,
            push_to_sap=body.push_to_sap,
            package=body.package,
            create_package_if_missing=body.create_package_if_missing,
            transport_request=body.transport_request,
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/cds/diagnose", operation_id="diagnose_cds_issue")
async def rest_diagnose_cds_issue(body: CdsViewNameRequest):
    try:
        return await abap_client.diagnose_cds_issue(body.view_name)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/cds/autofix", operation_id="auto_fix_cds_view")
async def rest_auto_fix_cds_view(body: CdsViewNameRequest):
    try:
        return await abap_client.auto_fix_cds_view(body.view_name)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/cds/push_fix", operation_id="push_cds_fix")
async def rest_push_cds_fix(body: CdsPushFixRequest):
    try:
        return await abap_client.push_cds_view_to_sap(
            view_name=body.view_name,
            ddl=body.ddl,
            package=body.package,
            transport_request=body.transport_request,
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class AbapSummaryRequest(BaseModel):
    code: str


class CdsExplainRequest(BaseModel):
    raw_error: str


class CdsEnglishPromptRequest(BaseModel):
    prompt_text: str
    package: str = "$TMP"
    transport_request: str | None = None
    expose_to_fiori: bool = True
    push_to_sap: bool = False


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]


@app.post("/api/abap/summary", operation_id="summarize_abap_logic")
async def rest_abap_summary(body: AbapSummaryRequest):
    return {"summary": await ai_engine.summarize_abap_logic(body.code)}


@app.post("/api/abap/optimize", operation_id="optimize_abap_code")
async def rest_abap_optimize(body: AbapSummaryRequest):
    return {"optimization": await ai_engine.optimize_abap_code(body.code)}


@app.post("/api/chat", operation_id="chat_ai")
async def rest_chat(body: ChatRequest):
    return {"reply": await ai_engine.chat_with_ollama(body.messages)}


@app.post("/api/cds/explain_diagnosis", operation_id="explain_cds_diagnosis")
async def rest_cds_explain(body: CdsExplainRequest):
    return {"explanation": await ai_engine.explain_cds_diagnosis(body.raw_error)}


@app.post("/api/cds/generate_from_english", operation_id="generate_cds_from_english")
async def rest_cds_generate_from_english(body: CdsEnglishPromptRequest):
    result = await ai_engine.generate_cds_from_english(body.prompt_text)
    if "error" in result:
        return result

    try:
        return await abap_client.create_cds_view(
            view_name=result.get("view_name"),
            table_name=result.get("table_name"),
            fields=result.get("fields", []),
            joins=result.get("joins", []),
            expose_to_fiori=body.expose_to_fiori,
            push_to_sap=body.push_to_sap,
            package=body.package,
            transport_request=body.transport_request,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
async def health():
    return {"status": "ok", "modes": ["rest:/api/*", "mcp:/mcp (streamable-http)", "mcp:/sse (sse)"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
