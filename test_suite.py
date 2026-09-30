"""
test_suite.py
-------------
Automated unit & integration test suite for ABAP & CDS Agent features:
1. Multi-table CDS view generation (JOINs, Associations, SQL view names)
2. Single-table CDS view generation (backward compatibility)
3. ST22 auto-fix proposal generation (user review mode)
4. User-controlled push_abap_fix logic (confirm_push=False vs confirm_push=True)
5. SAP Package creation & user-selected custom package handling
6. REST API endpoints testing via FastAPI TestClient
7. YAML Validator check via deploy.py
"""

import sys
import asyncio
from fastapi.testclient import TestClient

import abap_client
from server import app
import deploy


def test_cds_single_table_ddl():
    """Verify single table CDS generation produces valid SAP DDL syntax."""
    res = asyncio.run(
        abap_client.create_cds_view(
            view_name="Z_I_SingleTest",
            table_name="vbak",
            fields=["vbeln as SalesOrder", "erdat as CreationDate"],
            expose_to_fiori=True,
            push_to_sap=False,
        )
    )
    assert res["view_name"] == "Z_I_SingleTest"
    assert res["sql_view_name"] == "ZSQL_I_SINGLETEST"[:16]
    ddl = res["ddl"]
    assert "@AbapCatalog.sqlViewName:" in ddl
    assert "@OData.publish: true" in ddl
    assert "define view Z_I_SingleTest" in ddl
    assert "as select from vbak" in ddl
    assert "vbeln as SalesOrder" in ddl
    print("[TEST PASS] Single-table CDS View DDL verified!")


def test_cds_multi_table_ddl():
    """Verify multi-table CDS generation with JOINs and Associations."""
    joins = [
        {
            "table": "vbap",
            "alias": "Item",
            "join_type": "left outer join",
            "on": "Header.vbeln = Item.vbeln",
        }
    ]
    associations = [
        {
            "target": "kna1",
            "alias": "_Customer",
            "cardinality": "[0..*]",
            "on": "$projection.CustomerNumber = _Customer.kunnr",
        }
    ]
    fields = [
        "key Header.vbeln as SalesOrder",
        "Header.kunnr as CustomerNumber",
        "Item.posnr as ItemNumber",
        "Item.netwr as NetAmount",
        "_Customer",
    ]

    res = asyncio.run(
        abap_client.create_cds_view(
            view_name="Z_I_MultiTest",
            table_name="vbak as Header",
            fields=fields,
            joins=joins,
            associations=associations,
            sql_view_name="ZSQL_MULTITEST",
            expose_to_fiori=True,
            push_to_sap=False,
        )
    )
    assert res["view_name"] == "Z_I_MultiTest"
    assert res["sql_view_name"] == "ZSQL_MULTITEST"
    ddl = res["ddl"]
    assert "@AbapCatalog.sqlViewName: 'ZSQL_MULTITEST'" in ddl
    assert "left outer join vbap as Item on Header.vbeln = Item.vbeln" in ddl
    assert "association [0..*] to kna1 as _Customer on $projection.CustomerNumber = _Customer.kunnr" in ddl
    assert "key Header.vbeln as SalesOrder" in ddl
    print("[TEST PASS] Multi-table CDS View DDL with JOINs & Associations verified!")


def test_st22_autofix_proposal():
    """Verify auto_fix_abap returns a proposal awaiting user approval."""
    async def mock_analyze(dump_id):
        return {
            "dump_id": dump_id,
            "raw_response": '<dump:dump title="Runtime Error: CX_SY_ZERODIVIDE" terminatedProgram="ZTEST_PROG"/>',
        }

    orig_fn = abap_client.analyze_st22_dump
    abap_client.analyze_st22_dump = mock_analyze
    try:
        res = asyncio.run(abap_client.auto_fix_abap("DUMP_TEST_123"))
        assert res["status"] == "PROPOSED"
        assert res["target_program"] == "ZTEST_PROG"
        assert res["exception_type"] == "CX_SY_ZERODIVIDE"
        assert res["requires_user_approval"] is True
        assert res["push_ready"] is True
        assert "Fix proposal generated" in res["user_controller_message"]
        print("[TEST PASS] ST22 auto_fix_abap proposal mode verified!")
    finally:
        abap_client.analyze_st22_dump = orig_fn


def test_user_controlled_push_abap_fix():
    """Verify push_abap_fix respects confirm_push user controller flag."""
    res1 = asyncio.run(
        abap_client.push_abap_fix(
            program_name="ZTEST_PROG",
            fixed_code="WRITE 'Hello'.",
            confirm_push=False,
        )
    )
    assert res1["pushed"] is False
    assert res1["status"] == "AWAITING_USER_APPROVAL"
    assert "user confirmation is required" in res1["message"]

    print("[TEST PASS] User controller blocked push when confirm_push=False!")


def test_create_sap_package():
    """Verify create_sap_package produces valid ADT package XML payload."""
    res = asyncio.run(
        abap_client.create_sap_package(
            package_name="ZDEV_CUSTOM_PKG",
            description="Custom Package for CDS Views",
            push_to_sap=False,
        )
    )
    assert res["package_name"] == "ZDEV_CUSTOM_PKG"
    xml = res["package_xml"]
    assert "<pak:package" in xml
    assert 'adtcore:name="ZDEV_CUSTOM_PKG"' in xml
    print("[TEST PASS] SAP Package creation payload verified!")


def test_fastapi_rest_endpoints():
    """Test FastAPI REST endpoints using TestClient."""
    client = TestClient(app)

    # Health check
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"

    # Package Create REST endpoint
    pkg_payload = {
        "package_name": "ZREST_PKG",
        "description": "Rest Package",
        "push_to_sap": False,
    }
    r_pkg = client.post("/api/package/create", json=pkg_payload)
    assert r_pkg.status_code == 200
    assert r_pkg.json()["package_name"] == "ZREST_PKG"

    # CDS Create REST endpoint (multi-table + custom package)
    cds_payload = {
        "view_name": "Z_I_RestTest",
        "table_name": "vbak as Header",
        "fields": ["Header.vbeln as SalesOrder", "Item.posnr as ItemNumber"],
        "joins": [
            {
                "table": "vbap",
                "alias": "Item",
                "join_type": "left outer join",
                "on": "Header.vbeln = Item.vbeln",
            }
        ],
        "expose_to_fiori": True,
        "package": "ZDEV_CUSTOM_PKG",
        "create_package_if_missing": True,
        "push_to_sap": False,
    }
    r_cds = client.post("/api/cds/create", json=cds_payload)
    assert r_cds.status_code == 200
    data = r_cds.json()
    assert data["view_name"] == "Z_I_RestTest"
    assert "left outer join vbap" in data["ddl"]

    # Push Fix REST endpoint (confirm_push=False check)
    push_payload = {
        "program_name": "ZTEST_PROG",
        "fixed_code": "IF lv_val <> 0. ENDIF.",
        "confirm_push": False,
    }
    r_push = client.post("/api/abap/push_fix", json=push_payload)
    assert r_push.status_code == 200
    assert r_push.json()["pushed"] is False
    assert r_push.json()["status"] == "AWAITING_USER_APPROVAL"

    print("[TEST PASS] All FastAPI REST endpoints verified successfully!")


def test_deploy_joule_validator():
    """Verify Joule Agent deploy validator script runs cleanly."""
    res = deploy.main([])
    assert res == 0
    print("[TEST PASS] Joule Agent deploy validator verified!")


def test_cds_autofix_missing_key():
    """Verify auto_fix_cds_view auto-adds missing key keyword to CDS views."""
    async def mock_diagnose(view_name):
        return {
            "view_name": view_name,
            "ddl_source": "define view entity ZCDS_CASE as select from vbak {\n  vbak.vbeln,\n  vbak.erdat\n}",
            "issues": [],
            "checkrun_processed": True,
            "status": "SUCCESS"
        }

    orig_fn = abap_client.diagnose_cds_issue
    abap_client.diagnose_cds_issue = mock_diagnose
    try:
        res = asyncio.run(abap_client.auto_fix_cds_view("ZCDS_CASE"))
        assert "key vbak.vbeln" in res["repaired_ddl"]
        assert any("key" in fix for fix in res["applied_fixes"])
        print("[TEST PASS] CDS View auto-repair missing 'key' keyword verified!")
    finally:
        abap_client.diagnose_cds_issue = orig_fn


def test_push_cds_fix_endpoint():
    """Verify CDS push_fix REST endpoint accepts repaired DDL payload."""
    client = TestClient(app)
    payload = {
        "view_name": "ZCDS_FIXTEST",
        "ddl": "define view entity ZCDS_FIXTEST as select from vbak { key vbeln }",
        "package": "$TMP"
    }
    r = client.post("/api/cds/push_fix", json=payload)
    assert r.status_code == 200
    print("[TEST PASS] CDS Push Fix REST endpoint verified successfully!")


def test_mcp_connection_and_lifespan():
    """Verify MCP streamable-http initialize handshake succeeds with lifespan active."""
    with TestClient(app) as client:
        init_payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-suite", "version": "1.0.0"}
            },
            "id": 1
        }
        r = client.post(
            "/mcp/",
            json=init_payload,
            headers={
                "Accept": "text/event-stream, application/json",
                "Content-Type": "application/json"
            }
        )
        assert r.status_code == 200
        assert "jsonrpc" in r.text
        print("[TEST PASS] MCP Streamable-HTTP initialize handshake verified!")


def test_mock_mode_end_to_end():
    """Verify that Mock Mode runs all operations without physical SAP backend dependency."""
    # 1. Recent dumps in mock mode
    dumps = asyncio.run(abap_client.list_recent_dumps(max_results=5))
    assert dumps["error"] is False
    assert len(dumps["dumps"]) >= 2
    first_dump_id = dumps["dumps"][0]["dump_id"]

    # 2. Analyze ST22 dump in mock mode
    analysis = asyncio.run(abap_client.analyze_st22_dump(first_dump_id))
    assert analysis["dump_id"] == first_dump_id
    assert "COMPUTE_INT_ZERODIVIDE" in analysis["raw_response"]

    # 3. Auto-fix ABAP in mock mode
    proposal = asyncio.run(abap_client.auto_fix_abap(first_dump_id))
    assert proposal["status"] == "PROPOSED"
    assert proposal["exception_type"] == "CX_SY_ZERODIVIDE"

    # 4. Push ABAP fix with confirm_push=True in mock mode
    push_res = asyncio.run(abap_client.push_abap_fix("ZTEST_CALCULATOR", "WRITE 1.", confirm_push=True))
    assert push_res["status"] == "SUCCESS"
    assert push_res["pushed"] is True
    assert "activated" in push_res["steps_completed"]

    # 5. CDS Diagnose and push in mock mode
    diag = asyncio.run(abap_client.diagnose_cds_issue("Z_BROKEN_CDS"))
    assert diag["status"] == "SUCCESS"
    assert len(diag["issues"]) > 0

    repaired = asyncio.run(abap_client.auto_fix_cds_view("Z_BROKEN_CDS"))
    assert repaired["status"] == "SUCCESS"
    assert len(repaired["applied_fixes"]) > 0

    print("[TEST PASS] Full end-to-end mock mode workflow verified with zero errors!")


def test_ai_intelligence_endpoints():
    """Verify AI summarization, optimization, diagnosis explanation, and natural language CDS generation."""
    client = TestClient(app)

    # 1. ABAP Summary
    code_snippet = "REPORT ztest.\nSELECT vbeln FROM vbak INTO TABLE @DATA(lt_vbak).\nLOOP AT lt_vbak INTO DATA(ls_vbak).\nENDLOOP."
    r_sum = client.post("/api/abap/summary", json={"code": code_snippet})
    assert r_sum.status_code == 200
    assert "summary" in r_sum.json()
    assert len(r_sum.json()["summary"]) > 20

    # 2. ABAP Optimization
    r_opt = client.post("/api/abap/optimize", json={"code": code_snippet})
    assert r_opt.status_code == 200
    assert "optimization" in r_opt.json()

    # 3. CDS Explain Diagnosis
    r_exp = client.post("/api/cds/explain_diagnosis", json={"raw_error": "Element vbeln missing key designation"})
    assert r_exp.status_code == 200
    assert "key" in r_exp.json()["explanation"].lower()

    # 4. Natural language to CDS View
    r_gen = client.post(
        "/api/cds/generate_from_english",
        json={"prompt_text": "Sales order view from VBAK with items from VBAP", "push_to_sap": False}
    )
    assert r_gen.status_code == 200
    cds_res = r_gen.json()
    assert "view_name" in cds_res
    assert "ddl" in cds_res

    # 5. AI Chat
    r_chat = client.post("/api/chat", json={"messages": [{"role": "user", "content": "How do I fix ST22 dumps?"}]})
    assert r_chat.status_code == 200
    assert "reply" in r_chat.json()

    print("[TEST PASS] All AI intelligence endpoints verified successfully!")


if __name__ == "__main__":
    print("\n==========================================================")
    print("   RUNNING ABAP & CDS AGENT AUTOMATED SUITE")
    print("==========================================================\n")
    test_cds_single_table_ddl()
    test_cds_multi_table_ddl()
    test_st22_autofix_proposal()
    test_user_controlled_push_abap_fix()
    test_create_sap_package()
    test_fastapi_rest_endpoints()
    test_deploy_joule_validator()
    test_cds_autofix_missing_key()
    test_push_cds_fix_endpoint()
    test_mcp_connection_and_lifespan()
    test_mock_mode_end_to_end()
    test_ai_intelligence_endpoints()
    print("\n==========================================================")
    print("  ALL 12 TEST CASES PASSED SUCCESSFULLY (100% SUCCESS)!")
    print("==========================================================\n")
