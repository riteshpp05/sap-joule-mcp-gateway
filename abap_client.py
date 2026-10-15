"""
abap_client.py
--------------
Enterprise Facade for SAP S/4HANA & NetWeaver ABAP Development Tools (ADT).
Provides backward-compatible interfaces to modular domain services:
- ST22 short dump triage & crash remediation (services.st22_service)
- Core Data Services (CDS) DDL compilation & diagnostics (services.cds_service)
- CTS Change and Transport System governance (services.cts_service)
- ABAP Unit automated regression testing (services.unit_test_service)
- Data-driven mock engine (services.mock_provider)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from config.settings import settings
from config.constants import LOCAL_PACKAGE_DEFAULT
from core.exceptions import LockConflictError
from services.adt_client import adt_client
from services.cds_service import cds_service
from services.cts_service import cts_service
from services.mock_provider import mock_provider
from services.st22_service import st22_service
from services.unit_test_service import unit_test_service

# Exported Configuration Properties (Dynamic from Settings)
SAP_BASE_URL = settings.sap_base_url
SAP_CLIENT = settings.sap_client
SAP_USERNAME = settings.sap_username
SAP_PASSWORD = settings.sap_password
SAP_VERIFY_SSL = settings.sap_verify_ssl
SAP_MOCK_MODE = settings.sap_mock_mode


# ---------------------------------------------------------------------------
# ST22 Short Dump & ABAP Source Operations
# ---------------------------------------------------------------------------

async def fetch_abap_source(program: str) -> Dict[str, Any]:
    """Retrieves ABAP source code for a program."""
    return await st22_service.fetch_abap_source(program)


async def list_recent_dumps(max_results: int = 20) -> Dict[str, Any]:
    """Retrieves recent ST22 short dumps."""
    return await st22_service.list_recent_dumps(max_results)


async def analyze_st22_dump(dump_id: str) -> Dict[str, Any]:
    """Analyzes an ST22 dump by ID and returns XML diagnostics."""
    return await st22_service.analyze_st22_dump(dump_id)


async def auto_fix_abap(dump_id: str) -> Dict[str, Any]:
    """Generates an auto-fix proposal for human review before deployment."""
    return await st22_service.auto_fix_abap(dump_id, analyze_fn=analyze_st22_dump)


async def push_abap_fix(
    program_name: str,
    fixed_code: str,
    dump_id: Optional[str] = None,
    confirm_push: bool = False,
    package: str = LOCAL_PACKAGE_DEFAULT,
    transport_request: Optional[str] = None,
    run_unit_tests: bool = True,
    auto_rollback_on_test_failure: bool = True,
    simulate_activation_failure: bool = False,
) -> Dict[str, Any]:
    """Pushes an approved fix to SAP with CTS transport checks, lock checks, and rollback."""
    return await st22_service.push_abap_fix(
        program_name=program_name,
        fixed_code=fixed_code,
        dump_id=dump_id,
        confirm_push=confirm_push,
        package=package,
        transport_request=transport_request,
        run_unit_tests=run_unit_tests,
        auto_rollback_on_test_failure=auto_rollback_on_test_failure,
        simulate_activation_failure=simulate_activation_failure,
    )


# ---------------------------------------------------------------------------
# CDS View Operations
# ---------------------------------------------------------------------------

async def create_cds_view(
    view_name: str,
    table_name: str,
    fields: List[str],
    joins: Optional[List[Dict[str, str]]] = None,
    associations: Optional[List[Dict[str, str]]] = None,
    sql_view_name: Optional[str] = None,
    view_type: str = "classic",
    expose_to_fiori: bool = True,
    push_to_sap: bool = False,
    package: str = LOCAL_PACKAGE_DEFAULT,
    create_package_if_missing: bool = False,
    transport_request: Optional[str] = None,
) -> Dict[str, Any]:
    """Compiles CDS view DDL and optionally deploys to SAP ADT."""
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


async def diagnose_cds_issue(view_name: str) -> Dict[str, Any]:
    """Diagnoses why a CDS view failed to activate."""
    return await cds_service.diagnose_cds_issue(view_name)


async def auto_fix_cds_view(view_name: str, ddl_source: Optional[str] = None) -> Dict[str, Any]:
    """Automatically repairs common syntax errors in CDS DDL."""
    return await cds_service.auto_fix_cds_view(view_name, ddl_source=ddl_source, diagnose_fn=diagnose_cds_issue)


async def push_cds_view_to_sap(
    view_name: str,
    ddl: str,
    package: str = LOCAL_PACKAGE_DEFAULT,
    transport_request: Optional[str] = None,
) -> Dict[str, Any]:
    """Pushes an approved repaired CDS view live to SAP ADT."""
    return await cds_service.push_cds_view_to_sap(
        view_name=view_name,
        ddl=ddl,
        package=package,
        transport_request=transport_request,
    )


# ---------------------------------------------------------------------------
# CTS Transport & Package Governance
# ---------------------------------------------------------------------------

def validate_transport_request(transport_request: Optional[str] = None, package: str = LOCAL_PACKAGE_DEFAULT) -> Dict[str, Any]:
    """Validates transport request compliance against SAP CTS conventions."""
    return cts_service.validate_transport_request(transport_request, package=package)


async def create_sap_package(
    package_name: str,
    description: Optional[str] = None,
    software_component: str = "HOME",
    transport_layer: str = "SAP",
    super_package: Optional[str] = None,
    transport_request: Optional[str] = None,
    push_to_sap: bool = True,
) -> Dict[str, Any]:
    """Creates a new SAP development package via ADT."""
    return await cts_service.create_sap_package(
        package_name=package_name,
        description=description,
        software_component=software_component,
        transport_layer=transport_layer,
        super_package=super_package,
        transport_request=transport_request,
        push_to_sap=push_to_sap,
    )


# ---------------------------------------------------------------------------
# ABAP Unit Regression Testing
# ---------------------------------------------------------------------------

async def run_abap_unit_tests(program_name: str) -> Dict[str, Any]:
    """Executes ABAP Unit test suite for quality gate verification."""
    return await unit_test_service.run_abap_unit_tests(program_name)