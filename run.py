"""
run.py
------
Local Development Server Launcher.
Starts the unified dual-mode REST & FastMCP ASGI server gateway.
"""

from __future__ import annotations

import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))

    print("==========================================================")
    print("   SAP JOULE AI AGENT - GATEWAY SERVER (REST + FastMCP)   ")
    print("==========================================================")
    print(f"  * Web Studio Dashboard:     http://{host}:{port}/")
    print(f"  * Interactive Swagger Docs: http://{host}:{port}/docs")
    print(f"  * Local OpenAPI Spec URL:   http://{host}:{port}/openapi.json")
    print(f"  * FastMCP Streamable-HTTP:  http://{host}:{port}/mcp")
    print(f"  * FastMCP Server-Sent Events: http://{host}:{port}/sse")
    print("==========================================================\n")
    uvicorn.run("server:app", host=host, port=port, reload=True)
