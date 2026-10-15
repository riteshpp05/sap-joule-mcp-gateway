# SAP Joule & MCP Dual-Mode ABAP/CDS Debug Gateway

A production-grade, enterprise dual-mode API gateway and agent server connecting **SAP Joule / MCP AI Clients** to **SAP S/4HANA & BTP ABAP Development Tools (ADT)** for automated ST22 crash dump triage, rule-based code repair, atomic rollback deployments, and modern CDS View Entity generation.

---

## Why This Problem Matters (Business & Technical Value)

1. **Eliminates High-Severity Downtime (ST22 Dumps)**: In enterprise SAP environments, runtime short dumps (`COMPUTE_INT_ZERODIVIDE`, `CX_SY_REF_IS_INITIAL`, `CONVT_NO_NUMBER`) crash critical batch jobs and Fiori apps. Manually navigating `ST22` and locating broken lines in `SE38` inflates MTTR. This gateway automates dump inspection and proposes syntax-checked fixes in seconds.
2. **Atomic Rollback & Safety**: If code activation fails or post-activation ABAP Unit tests detect a regression, the gateway automatically executes an **atomic rollback**, restoring original active source code to prevent production outages.
3. **Enterprise CTS / ChaRM Governance**: Enforces strict SAP Transport Request (`corrNr`) validation for all non-local packages, maintaining complete SOX and ITIL audit trails.
4. **Modern S/4HANA CDS View Entities**: Supports modern `define view entity` (ABAP 7.55+ / S/4HANA) without legacy 16-character SQL view limitations, alongside backward-compatible classic CDS view definitions.
5. **Bridge Between AI and SAP Kernels**: Bridges modern AI protocols (**FastMCP** Streamable-HTTP & SSE) and enterprise REST (**OpenAPI 3.0**) to SAP ADT REST services (`/sap/bc/adt/*`).
6. **Enterprise Observability & Security**: Includes Prometheus metrics (`/metrics`), Kubernetes/BTP liveness and readiness health probes (`/health/live`, `/health/ready`), request correlation tracking (`X-Correlation-ID`), and optional API Key guards.

---

## Project Structure & File Map

```text
├── server.py                        # Unified ASGI Gateway (FastAPI REST + FastMCP + Metrics & Probes)
├── ai_engine.py                     # Multi-tier intelligence engine (Ollama -> Gemini -> Heuristic fallback)
├── abap_client.py                   # SAP ADT client, atomic rollback, AUnit gate, & mock engine
├── btp_proxy.py                     # BTP Connectivity service proxy with OAuth token caching
├── deploy.py                        # CLI tool for manifest validation and tenant package creation
├── run.py                           # Local server launcher
├── main.py                          # Standard ASGI application entrypoint
├── test_suite.py                    # Automated test suite (18 enterprise production test cases)
├── Dockerfile                       # Multi-stage production container image
├── .dockerignore                    # Container build exclusion list
├── .github/workflows/ci.yml         # GitHub Actions automated test & package pipeline
├── abap_cds_agent.da.sapdas.yaml    # SAP Joule Agent manifest (SAPDAS 3.4.0)
├── abap_cds_capability/
│   ├── capability.sapdas.yaml       # Joule capability specification
│   ├── openapi.json                 # OpenAPI 3.0.3 specification (17 endpoints)
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
GATEWAY_API_KEY=
ALLOWED_ORIGINS=*
```

### 3. Run Automated Production Test Suite
```bash
python test_suite.py
```
*Executes all 18 test cases verifying CDS View Entities, atomic rollback, lock conflicts, ABAP Unit regression testing, CTS transport governance, mock modes, Prometheus metrics, and MCP handshakes.*

### 4. Start Server
```bash
python run.py
```
- **Web Cockpit**: `http://127.0.0.1:8080/`
- **Interactive Swagger Docs**: `http://127.0.0.1:8080/docs`
- **OpenAPI 3.0 Spec**: `http://127.0.0.1:8080/openapi.json`
- **Prometheus Metrics**: `http://127.0.0.1:8080/metrics`
- **Liveness Probe**: `http://127.0.0.1:8080/health/live`
- **Readiness Probe**: `http://127.0.0.1:8080/health/ready`
- **MCP Streamable-HTTP**: `http://127.0.0.1:8080/mcp`
- **MCP Server-Sent Events**: `http://127.0.0.1:8080/sse`

---

## Docker Deployment

To build and run the production container:
```bash
docker build -t sap-joule-mcp-gateway:latest .
docker run -p 8080:8080 --env-file .env sap-joule-mcp-gateway:latest
```

---

## SAP Joule Deployment

To validate manifests and generate the tenant upload package:
```bash
python deploy.py --package
```
This validates all schemas and builds `abap_cds_agent.zip` for direct upload in **SAP Joule Developer Center / BTP Tenant**.
