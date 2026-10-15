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


def test_cds_view_entity_modernization():
    """Verify modern CDS View Entity generation vs Classic CDS Views."""
    # Test 1: Modern View Entity (default)
    res_entity = asyncio.run(
        abap_client.create_cds_view(
            view_name="Z_I_EntityTest",
            table_name="vbak",
            fields=["key vbeln as SalesOrder", "erdat as CreationDate"],
            view_type="entity",
            push_to_sap=False,
        )
    )
    assert res_entity["view_type"] == "entity"
    assert res_entity["sql_view_name"] is None
    assert "define view entity Z_I_EntityTest" in res_entity["ddl"]
    assert "@AbapCatalog.sqlViewName" not in res_entity["ddl"]

    # Test 2: Classic CDS View (backward compatibility)
    res_classic = asyncio.run(
        abap_client.create_cds_view(
            view_name="Z_I_ClassicTest",
            table_name="vbak",
            fields=["key vbeln as SalesOrder"],
            view_type="classic",
            push_to_sap=False,
        )
    )
    assert res_classic["view_type"] == "classic"
    assert res_classic["sql_view_name"] is not None
    assert "define view Z_I_ClassicTest" in res_classic["ddl"]
    assert "@AbapCatalog.sqlViewName:" in res_classic["ddl"]
    print("[TEST PASS] CDS View Entity & Classic DDL modernization verified!")


def test_transport_request_governance():
    """Verify CTS Transport Request validation rules."""
    # 1. Local package ($TMP) does not require TR
    v1 = abap_client.validate_transport_request(None, package="$TMP")
    assert v1["valid"] is True
    assert v1["is_local"] is True

    # 2. Non-local package without TR is rejected
    v2 = abap_client.validate_transport_request(None, package="ZDEV_PACKAGE")
    assert v2["valid"] is False
    assert "mandates an active Transport Request" in v2["message"]

    # 3. Invalid TR format is rejected
    v3 = abap_client.validate_transport_request("BAD_TR_FORMAT", package="ZDEV_PACKAGE")
    assert v3["valid"] is False
    assert "Invalid Transport Request format" in v3["message"]

    # 4. Valid TR format is accepted
    v4 = abap_client.validate_transport_request("DEVK900123", package="ZDEV_PACKAGE")
    assert v4["valid"] is True
    assert v4["transport_request"] == "DEVK900123"

    print("[TEST PASS] Enterprise CTS Transport Request Governance verified!")


def test_automated_rollback_on_activation_failure():
    """Verify atomic automated rollback if activation fails."""
    res = asyncio.run(
        abap_client.push_abap_fix(
            program_name="ZTEST_CALCULATOR",
            fixed_code="REPORT ztest.\nWRITE 'Invalid Syntax'.",
            confirm_push=True,
            simulate_activation_failure=True,
        )
    )
    assert res["status"] == "ROLLED_BACK"
    assert res["rollback_performed"] is True
    assert res["activated"] is False
    assert "Automated rollback executed" in res["message"]
    print("[TEST PASS] Automated Rollback on activation failure verified!")


def test_lock_conflict_handling():
    """Verify concurrency conflict detection with user attribution."""
    res = asyncio.run(
        abap_client.push_abap_fix(
            program_name="Z_LOCKED_PROGRAM",
            fixed_code="REPORT z_locked.\nWRITE 1.",
            confirm_push=True,
        )
    )
    assert res["status"] == "LOCK_CONFLICT"
    assert res["lock_conflict"] is True
    assert res["locked_by"] == "BASIS_ADMIN"
    assert "locked by SAP user" in res["message"]
    print("[TEST PASS] Concurrency Lock Conflict handling verified!")


def test_abap_unit_regression_gate():
    """Verify ABAP Unit automated regression testing and rollback triggers."""
    # 1. Normal run with passing tests
    u_pass = asyncio.run(abap_client.run_abap_unit_tests("ZTEST_CALCULATOR"))
    assert u_pass["status"] == "SUCCESS"
    assert u_pass["passed"] > 0
    assert u_pass["failed"] == 0

    # 2. Regression detected and rollback triggered
    u_fail = asyncio.run(
        abap_client.push_abap_fix(
            program_name="Z_FAIL_CALCULATOR",
            fixed_code="REPORT z_fail.\nWRITE 1.",
            confirm_push=True,
            run_unit_tests=True,
            auto_rollback_on_test_failure=True,
        )
    )
    assert u_fail["status"] == "ROLLED_BACK_ON_TEST_FAILURE"
    assert u_fail["rollback_performed"] is True
    assert "regression detected" in u_fail["message"].lower()
    print("[TEST PASS] ABAP Unit Regression Gate and Rollback verified!")


def test_observability_metrics_and_health_probes():
    """Verify Prometheus metrics endpoint, liveness/readiness probes, and correlation headers."""
    client = TestClient(app)

    # 1. Liveness probe
    r_live = client.get("/health/live")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "ALIVE"

    # 2. Readiness probe
    r_ready = client.get("/health/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "READY"

    # 3. Correlation ID header propagation
    test_corr_id = "test-corr-uuid-9988"
    r_corr = client.get("/health", headers={"X-Correlation-ID": test_corr_id})
    assert r_corr.headers.get("X-Correlation-ID") == test_corr_id
    assert "X-Response-Time" in r_corr.headers

    # 4. Prometheus metrics endpoint
    r_metrics = client.get("/metrics")
    assert r_metrics.status_code == 200
    assert "gateway_requests_total" in r_metrics.text
    assert "sap_rollbacks_total" in r_metrics.text

    # 5. CTS validation endpoint
    r_cts = client.post("/api/cts/validate", json={"package": "$TMP"})
    assert r_cts.status_code == 200
    assert r_cts.json()["valid"] is True

    # 6. Unit tests endpoint
    r_u = client.post("/api/abap/unit_tests", json={"program_name": "ZTEST_CALC"})
    assert r_u.status_code == 200
    assert r_u.json()["status"] == "SUCCESS"

    print("[TEST PASS] Observability, Metrics, and Health Probes verified!")


if __name__ == "__main__":
    print("\n==========================================================")
    print("   RUNNING ABAP & CDS AGENT AUTOMATED PRODUCTION SUITE")
    print("==========================================================\n")
    test_cds_single_table_ddl()
    test_cds_multi_table_ddl()
    test_cds_view_entity_modernization()
    test_st22_autofix_proposal()
    test_user_controlled_push_abap_fix()
    test_transport_request_governance()
    test_automated_rollback_on_activation_failure()
    test_lock_conflict_handling()
    test_abap_unit_regression_gate()
    test_create_sap_package()
    test_fastapi_rest_endpoints()
    test_deploy_joule_validator()
    test_cds_autofix_missing_key()
    test_push_cds_fix_endpoint()
    test_mcp_connection_and_lifespan()
    test_mock_mode_end_to_end()
    test_ai_intelligence_endpoints()
    test_observability_metrics_and_health_probes()
    print("\n==========================================================")
    print("  ALL 18 TEST CASES PASSED SUCCESSFULLY (100% SUCCESS)!")
    print("==========================================================\n")
