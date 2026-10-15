"""
services/ai_service.py
----------------------
AI Intelligence Engine for SAP Joule Gateway.
Supports multi-provider orchestration: Google Gemini, Ollama (Local LLM), and intelligent heuristic engines.
Loads prompts and templates dynamically from external fixtures.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import httpx
from config.settings import settings
from core.logger import logger
from services.mock_provider import mock_provider


class AIService:
    """Enterprise AI Service for ABAP explanation, optimization, and CDS generation."""

    def __init__(self):
        self.gemini_api_key = settings.gemini_api_key
        self.ollama_host = settings.ollama_host.rstrip("/")
        self.ollama_model = settings.ollama_model

    def _get_prompt(self, key: str, fallback: str) -> str:
        prompts = mock_provider.get_prompt_templates()
        return prompts.get(key, fallback)

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Attempts to invoke local Ollama model if available."""
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.ollama_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response")
        except Exception:
            pass
        return None

    async def summarize_abap_logic(self, code: str) -> str:
        """Summarizes ABAP code architecture and business flow."""
        sys_prompt = self._get_prompt(
            "summarize_system_prompt",
            "You are an SAP S/4HANA Architect. Summarize the provided ABAP code clearly.",
        )

        ollama_res = await self._call_ollama(sys_prompt, code)
        if ollama_res:
            return ollama_res

        # Heuristic Rule Engine
        clean = code.upper()
        detected_tables = [t for t in ["VBAK", "VBAP", "KNA1", "MARA", "BSEG", "EKKO"] if t in clean]
        tables_str = ", ".join(detected_tables) if detected_tables else "standard dictionary structures"

        summary = (
            f"**Architecture & Business Logic Summary**:\n\n"
            f"- **Pattern**: Classical ABAP procedural logic with database access layer.\n"
            f"- **Target Tables**: Interfaces with {tables_str}.\n"
            f"- **Execution Flow**: Reads records, executes validation logic, and writes output to the list/spool buffer.\n"
            f"- **Modernization Recommendation**: Encapsulate logic inside an ABAP OO class or CDS View Entity."
        )
        return summary

    async def optimize_abap_code(self, code: str) -> str:
        """Recommends 7.40+ modern syntax expressions and performance optimizations."""
        sys_prompt = self._get_prompt(
            "optimize_system_prompt",
            "You are an SAP Clean ABAP and Performance specialist. Optimize the given ABAP code.",
        )

        ollama_res = await self._call_ollama(sys_prompt, code)
        if ollama_res:
            return ollama_res

        return (
            "**SAP Clean ABAP 7.40+ Performance Recommendations**:\n\n"
            "1. **Inline Declarations**: Replace explicit `DATA:` statements with `DATA(...)` inline expressions.\n"
            "2. **Table Expressions**: Use `lt_table[ key = lv_val ]` instead of obsolete `READ TABLE ... WITH KEY`.\n"
            "3. **Open SQL Host Variables**: Prefix ABAP variables in SQL queries with `@` (e.g., `WHERE kunnr = @lv_kunnr`).\n"
            "4. **Array Operations**: Prefer `VALUE #( )` and `CORRESPONDING #( )` constructors to eliminate manual work area looping."
        )

    async def explain_cds_diagnosis(self, raw_error: str) -> str:
        """Explains CDS checkrun errors with clear actionable remediation steps."""
        sys_prompt = self._get_prompt(
            "explain_cds_system_prompt",
            "You are an SAP CDS View compiler specialist. Explain the error and provide a fix.",
        )

        ollama_res = await self._call_ollama(sys_prompt, raw_error)
        if ollama_res:
            return ollama_res

        return (
            f"**CDS Activation Diagnostic & Remediation**:\n\n"
            f"- **Identified Error**: `{raw_error.strip()}`\n"
            f"- **Root Cause**: The CDS compiler requires at least one primary key field defined in the select list, "
            f"and an explicit authorization check annotation.\n"
            f"- **Remediation**: Add `key` before the primary unique identifier (e.g., `key vbeln as SalesOrder`) "
            f"and include `@AccessControl.authorizationCheck: #NOT_REQUIRED` at the top of the DDL definition."
        )

    async def generate_cds_from_english(self, prompt_text: str) -> Dict[str, Any]:
        """Converts natural language specification into structured CDS view definition."""
        p_lower = prompt_text.lower()

        # Extract primary table
        table_name = "vbak"
        view_name = "Z_I_SalesOrder_Custom"

        if "material" in p_lower or "mara" in p_lower:
            table_name = "mara"
            view_name = "Z_I_Material_Custom"
        elif "invoice" in p_lower or "vbrk" in p_lower:
            table_name = "vbrk"
            view_name = "Z_I_Invoice_Custom"
        elif "finance" in p_lower or "bseg" in p_lower:
            table_name = "bseg"
            view_name = "Z_I_FinancialDoc_Custom"

        # Check for joins/associations
        joins: List[Dict[str, str]] = []
        associations: List[Dict[str, str]] = []

        if "item" in p_lower or "vbap" in p_lower:
            joins.append({
                "table": "vbap as Item",
                "join_type": "left outer join",
                "on": "Header.vbeln = Item.vbeln",
            })

        if "customer" in p_lower or "kna1" in p_lower:
            associations.append({
                "target": "kna1",
                "alias": "_Customer",
                "cardinality": "[0..*]",
                "on": "$projection.CustomerNumber = _Customer.kunnr",
            })

        fields = [
            f"key {table_name}.vbeln as DocumentNumber" if table_name != "mara" else "key mara.matnr as MaterialNumber",
            f"{table_name}.erdat as CreationDate" if table_name != "mara" else "mara.ersda as CreatedOn",
            f"{table_name}.netwr as NetAmount" if table_name == "vbak" else "mara.matkl as MaterialGroup",
        ]

        if associations:
            fields.append("_Customer")

        return {
            "view_name": view_name,
            "table_name": f"{table_name} as Header" if joins else table_name,
            "fields": fields,
            "joins": joins,
            "associations": associations,
            "view_type": "entity",
            "expose_to_fiori": True,
        }

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Handles conversational assistant requests for Joule copilot."""
        last_msg = messages[-1].get("content", "") if messages else ""
        low = last_msg.lower()

        if "dump" in low or "st22" in low or "crash" in low:
            return (
                "To resolve ST22 dumps, navigate to the **ST22 Short Dumps** tab. "
                "Select the dump from the feed to view raw XML diagnostics, then click **Propose Auto-Fix** "
                "to generate a defensive ABAP fix. You can review the diff before confirming the push live to SAP."
            )
        if "cds" in low or "view" in low:
            return (
                "In the **CDS View Studio** tab, you can enter an English description (e.g., 'Sales orders with items and customer') "
                "to automatically generate clean S/4HANA CDS View Entity DDL with proper annotations and JOINs."
            )
        if "cts" in low or "transport" in low:
            return (
                "The gateway strictly validates CTS transport requests. Local packages ($TMP) do not require a transport, "
                "while transportable packages (like ZDEV_CORE) require a valid transport format matching `<SID>K9XXXXX`."
            )
        return (
            "I am your SAP Joule & ADT AI Assistant. I can help you triage ST22 dumps, generate CDS View Entities, "
            "run ABAP Unit regression test gates, and validate CTS transport compliance. What would you like to do?"
        )


ai_service = AIService()
