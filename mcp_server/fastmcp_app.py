"""
mcp_server/fastmcp_app.py
-------------------------
FastMCP Tool Registrations and Streamable-HTTP / SSE Transport Handlers.
Exposes Model Context Protocol interfaces for SAP ADT operations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from services.cds_service import cds_service
from services.cts_service import cts_service
from services.st22_service import st22_service
from services.unit_test_service import unit_test_service
from services.ai_service import ai_service

mcp = FastMCP("abap_cds_debug_agent")


@mcp.tool()
async def fetch_abap_source(program: str) -> dict:
    """Fetch ABAP source code for a given program name."""
    return await st22_service.fetch_abap_source(program)


@mcp.tool()
async def analyze_st22_dump(dump_id: str) -> dict:
    """Analyze an ST22 short dump by dump ID."""
    return await st22_service.analyze_st22_dump(dump_id)


@mcp.tool()
async def list_recent_dumps(max_results: int = 20) -> dict:
    """List recent ST22 short dumps from SAP."""
    return await st22_service.list_recent_dumps(max_results)


@mcp.tool()
async def auto_fix_abap(dump_id: str) -> dict:
    """Propose an auto-fix for an ABAP short dump. Returns a proposal for user review."""
    return await st22_service.auto_fix_abap(dump_id)


@mcp.tool()
async def push_abap_fix(
    program_name: str,
    fixed_code: str,
    dump_id: Optional[str] = None,
    confirm_push: bool = False,
    package: str = "$TMP",
    transport_request: Optional[str] = None,
    run_unit_tests: bool = True,
    auto_rollback_on_test_failure: bool = True,
) -> dict:
    """Push an approved ABAP auto-fix live to SAP via ADT with regression gates and rollback."""
    return await st22_service.push_abap_fix(
        program_name=program_name,
        fixed_code=fixed_code,
        dump_id=dump_id,
        confirm_push=confirm_push,
        package=package,
        transport_request=transport_request,
        run_unit_tests=run_unit_tests,
        auto_rollback_on_test_failure=auto_rollback_on_test_failure,
    )


@mcp.tool()
async def run_abap_unit_tests(program_name: str) -> dict:
    """Run automated ABAP Unit regression tests for a program via SAP ADT."""
    return await unit_test_service.run_abap_unit_tests(program_name)


@mcp.tool()
async def validate_transport_request(transport_request: Optional[str] = None, package: str = "$TMP") -> dict:
    """Validate Transport Request compliance against enterprise SAP CTS/ChaRM rules."""
    return cts_service.validate_transport_request(transport_request, package=package)


@mcp.tool()
async def create_sap_package(
    package_name: str,
    description: Optional[str] = None,
    software_component: str = "HOME",
    transport_layer: str = "SAP",
    super_package: Optional[str] = None,
    transport_request: Optional[str] = None,
    push_to_sap: bool = True,
) -> dict:
    """Create a new SAP Development Package (DevClass) live in the SAP system via ADT."""
    return await cts_service.create_sap_package(
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
    joins: Optional[list[dict[str, str]]] = None,
    associations: Optional[list[dict[str, str]]] = None,
    sql_view_name: Optional[str] = None,
    view_type: str = "classic",
    expose_to_fiori: bool = True,
    push_to_sap: bool = False,
    package: str = "$TMP",
    create_package_if_missing: bool = False,
    transport_request: Optional[str] = None,
) -> dict:
    """Generate a new CDS view DDL definition supporting modern View Entities ('entity') or classic views ('classic')."""
    return await cds_service.create_cds_view(
        view_name=view_name,
        table_name=table_name,
        fields=fields,
        joins=joins,
        associations=associations,
        sql_view_name=sql_view_name,
        view_type=view_type,
        expose_to_fiori=expose_to_fiori,
        push_to_sap=push_to_sap,
        package=package,
        create_package_if_missing=create_package_if_missing,
        transport_request=transport_request,
    )


@mcp.tool()
async def diagnose_cds_issue(view_name: str) -> dict:
    """Diagnose why a CDS view failed to activate."""
    return await cds_service.diagnose_cds_issue(view_name)


@mcp.tool()
async def auto_fix_cds_view(view_name: str) -> dict:
    """Attempt to auto-repair a broken CDS view."""
    return await cds_service.auto_fix_cds_view(view_name)


@mcp.tool()
async def push_cds_fix(
    view_name: str,
    ddl: str,
    package: str = "$TMP",
    transport_request: Optional[str] = None,
) -> dict:
    """Push an approved repaired CDS view live to the SAP system via ADT."""
    return await cds_service.push_cds_view_to_sap(
        view_name=view_name,
        ddl=ddl,
        package=package,
        transport_request=transport_request,
    )


@mcp.tool()
async def summarize_abap_logic(code: str) -> dict:
    """Summarize the logic and architecture of an ABAP program in plain English."""
    summary = await ai_service.summarize_abap_logic(code)
    return {"summary": summary}


@mcp.tool()
async def optimize_abap_code(code: str) -> dict:
    """Analyze ABAP code and suggest 7.40+ modern syntax expressions and performance optimizations."""
    optimization = await ai_service.optimize_abap_code(code)
    return {"optimization": optimization}


@mcp.tool()
async def explain_cds_diagnosis(raw_error: str) -> dict:
    """Explain an SAP CDS View activation error with actionable step-by-step remediation advice."""
    explanation = await ai_service.explain_cds_diagnosis(raw_error)
    return {"explanation": explanation}


@mcp.tool()
async def generate_cds_from_english(
    prompt_text: str,
    package: str = "$TMP",
    transport_request: Optional[str] = None,
    expose_to_fiori: bool = True,
    push_to_sap: bool = False,
) -> dict:
    """Generate a CDS View definition from an English description and optionally deploy live to SAP."""
    result = await ai_service.generate_cds_from_english(prompt_text)
    if "error" in result:
        return result
    return await cds_service.create_cds_view(
        view_name=result.get("view_name"),
        table_name=result.get("table_name"),
        fields=result.get("fields", []),
        joins=result.get("joins", []),
        expose_to_fiori=expose_to_fiori,
        push_to_sap=push_to_sap,
        package=package,
        transport_request=transport_request,
    )


# FastMCP ASGI sub-applications
mcp_sh_app = mcp.http_app(path="/", transport="streamable-http")
mcp_sse_app = mcp.http_app(path="/", transport="sse")
