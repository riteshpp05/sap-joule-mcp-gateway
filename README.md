# SAP Joule & MCP Dual-Mode ABAP/CDS Debug Gateway

A production-grade, dual-mode API gateway and agent server connecting **SAP Joule / MCP AI Clients** to **SAP S/4HANA & BTP ABAP Development Tools (ADT)** for automated ST22 crash dump triage, rule-based code repair, and CDS View generation.

---

## Why This Problem Matters (Business & Technical Value)

1. **Eliminates High-Severity Downtime (ST22 Dumps)**: In enterprise SAP environments, runtime short dumps (`COMPUTE_INT_ZERODIVIDE`, `CX_SY_REF_IS_INITIAL`, `CONVT_NO_NUMBER`) crash critical batch jobs and Fiori apps. Manually navigating `ST22` and locating broken lines in `SE38` inflates MTTR. This gateway automates dump inspection and proposes syntax-checked fixes in seconds.
2. **Accelerates CDS View Data Modeling**: S/4HANA Virtual Data Models (VDMs) require extensive Core Data Services (CDS) DDL definitions. This tool parses English requirements into production-ready CDS syntax with proper annotations (`@AbapCatalog`, `@AccessControl`, `@OData.publish`), associations, and joins.
3. **Bridge Between AI and SAP Kernels**: Bridges modern AI protocols (**FastMCP** Streamable-HTTP & SSE) and enterprise REST (**OpenAPI 3.0**) to SAP ADT REST services (`/sap/bc/adt/*`).
4. **Human-in-the-Loop Governance**: Any state-modifying action (pushing code to SAP) requires explicit human controller confirmation (`confirm_push=true`), adhering to SOX and ITIL change-management standards.

---

## Project Structure & File Map

```text
├── server.py                        # Unified ASGI Gateway (FastAPI REST + FastMCP endpoints)
├── ai_engine.py                     # Multi-tier intelligence engine (Ollama -> Gemini -> Heuristic fallback)
├── abap_client.py                   # SAP ADT client & isolated high-fidelity mock engine
├── btp_proxy.py                     # BTP Connectivity service proxy with OAuth token caching
├── deploy.py                        # CLI tool for manifest validation and tenant package creation
├── run.py                           # Local server launcher
├── main.py                          # Standard ASGI application entrypoint
├── test_suite.py                    # Automated test suite (12 end-to-end test cases)
├── abap_cds_agent.da.sapdas.yaml    # SAP Joule Agent manifest (SAPDAS 3.4.0)
├── abap_cds_capability/
│   ├── capability.sapdas.yaml       # Joule capability specification
│   ├── openapi.json                 # OpenAPI 3.0.3 specification (15 endpoints)
│   └── scenarios/scenario.yaml      # Joule test scenario utterances
├── static/index.html                # Fiori Horizon developer web studio cockpit
├── manifest.yml                     # SAP BTP Cloud Foundry deployment manifest
├── Procfile                         # Cloud Foundry web process command
├── requirements.txt                 # Pinned Python dependencies
└── .env.example                     # Environment configuration template
```

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`. For local offline development or automated testing, keep `SAP_MOCK_MODE=true`:
```env
SAP_BASE_URL=https://sap-mock-gateway.internal:44300
SAP_CLIENT=100
SAP_USERNAME=MOCK_DEVELOPER
SAP_PASSWORD=MOCK_PASSWORD_ONLY
SAP_VERIFY_SSL=false
SAP_MOCK_MODE=true
OLLAMA_MODEL=qwen2.5:3b
```

### 3. Run Automated Tests
```bash
python test_suite.py
```
*Executes all 12 test cases verifying CDS generation, ST22 auto-fix, human-in-the-loop gates, mock modes, and MCP handshakes.*

### 4. Start Server
```bash
python run.py
```
- **Web Cockpit**: `http://127.0.0.1:8080/`
- **Interactive Swagger Docs**: `http://127.0.0.1:8080/docs`
- **OpenAPI 3.0 Spec**: `http://127.0.0.1:8080/openapi.json`
- **MCP Streamable-HTTP**: `http://127.0.0.1:8080/mcp`
- **MCP Server-Sent Events**: `http://127.0.0.1:8080/sse`

---

## SAP Joule Deployment

To validate manifests and generate the tenant upload package:
```bash
python deploy.py --package
```
This validates all schemas and builds `abap_cds_agent.zip` for direct upload in **SAP Joule Developer Center / BTP Tenant**.
