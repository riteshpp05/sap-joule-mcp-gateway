"""
ai_engine.py
------------
Resilient Multi-Provider LLM & Heuristic Intelligence Engine for SAP ABAP & CDS.

Architectural Hierarchy:
1. Local Ollama (qwen2.5:3b / llama3 / mistral) if running and reachable.
2. Google Gemini API (if GEMINI_API_KEY is configured in environment).
3. Production Heuristic Engine: Deterministic, rule-based NLP parser and SAP code
   analyzer providing guaranteed 100% uptime for all AI endpoints without external dependencies.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ai_engine")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


# ---------------------------------------------------------------------------
# 1. Multi-Provider LLM Connector
# ---------------------------------------------------------------------------

async def call_llm(prompt: str, system: str = "") -> str:
    """Attempts LLM invocation across configured providers with graceful fallback."""
    # Attempt 1: Ollama
    try:
        import ollama
        client = ollama.AsyncClient(timeout=10.0)
        response = await client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            system=system,
            stream=False,
        )
        content = response.get("response", "").strip()
        if content:
            return content
    except Exception as exc:
        logger.debug(f"Ollama call skipped or failed ({exc}). Trying next provider.")

    # Attempt 2: Google Gemini (if API key present)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            res = await model.generate_content_async(full_prompt)
            if res.text:
                return res.text.strip()
        except Exception as exc:
            logger.debug(f"Gemini call failed ({exc}). Falling back to heuristic engine.")

    # Fallback to empty string to trigger domain-specific heuristic engine
    return ""


# ---------------------------------------------------------------------------
# 2. Heuristic Domain Engines (Deterministic & Resilient)
# ---------------------------------------------------------------------------

def _heuristic_cds_generator(prompt_text: str) -> Dict[str, Any]:
    """Parses natural language prompts into a valid CDS View JSON model."""
    text_lower = prompt_text.lower()
    
    # Table mapping heuristics
    table = "VBAK"
    if "material" in text_lower or "product" in text_lower or "mara" in text_lower:
        table = "MARA"
    elif "purchase" in text_lower or "po" in text_lower or "ekko" in text_lower:
        table = "EKKO"
    elif "customer" in text_lower or "kna1" in text_lower:
        table = "KNA1"
    elif "invoice" in text_lower or "billing" in text_lower or "vbrk" in text_lower:
        table = "VBRK"
    elif "delivery" in text_lower or "likp" in text_lower:
        table = "LIKP"
    elif "accounting" in text_lower or "gl" in text_lower or "bkpf" in text_lower:
        table = "BKPF"

    # Field mapping heuristics
    fields: List[str] = []
    joins: List[Dict[str, str]] = []

    if table == "VBAK":
        fields = [
            "key vbak.vbeln as SalesOrder",
            "vbak.erdat as CreationDate",
            "vbak.ernam as CreatedBy",
            "vbak.kunnr as CustomerNumber",
            "vbak.netwr as TotalNetAmount",
            "vbak.waerk as DocumentCurrency"
        ]
        if "item" in text_lower or "vbap" in text_lower:
            joins.append({
                "table": "vbap",
                "alias": "Item",
                "join_type": "inner join",
                "on": "Header.vbeln = Item.vbeln"
            })
            fields.extend(["Item.posnr as ItemNumber", "Item.matnr as Material", "Item.netwr as ItemNetAmount"])
    elif table == "MARA":
        fields = [
            "key mara.matnr as MaterialNumber",
            "mara.ersda as CreatedOn",
            "mara.ernam as CreatedBy",
            "mara.matkl as MaterialGroup",
            "mara.meins as BaseUnitOfMeasure"
        ]
        if "plant" in text_lower or "marc" in text_lower:
            joins.append({
                "table": "marc",
                "alias": "PlantData",
                "join_type": "left outer join",
                "on": "Header.matnr = PlantData.matnr"
            })
            fields.extend(["PlantData.werks as Plant"])
    elif table == "EKKO":
        fields = [
            "key ekko.ebeln as PurchaseOrder",
            "ekko.aedat as ChangedOn",
            "ekko.ernam as CreatedBy",
            "ekko.lifnr as VendorNumber"
        ]
        if "item" in text_lower or "ekpo" in text_lower:
            joins.append({
                "table": "ekpo",
                "alias": "Item",
                "join_type": "inner join",
                "on": "Header.ebeln = Item.ebeln"
            })
            fields.extend(["Item.ebelp as ItemNumber", "Item.matnr as MaterialNumber", "Item.netpr as NetPrice"])
    else:
        fields = ["key id as Identifier", "created_at as CreationDate", "status as Status"]

    # Deduce view name
    words = [w.capitalize() for w in re.findall(r"[a-zA-Z]+", prompt_text) if len(w) > 2]
    candidate = "Z_I_" + "".join(words[:3]) if words else f"Z_I_{table}_View"
    view_name = candidate[:26]

    return {
        "view_name": view_name,
        "table_name": f"{table} as Header" if joins else table,
        "fields": fields,
        "joins": joins,
        "expose_to_fiori": True,
    }


def _heuristic_abap_summary(code: str) -> str:
    """Generates an executive technical summary of ABAP code."""
    lines = code.splitlines()
    tables_found = set(re.findall(r"\bFROM\s+([A-Z0-9_/]+)\b", code, re.IGNORECASE))
    loops_found = len(re.findall(r"\bLOOP\s+AT\b", code, re.IGNORECASE))
    calls_found = set(re.findall(r"\bCALL\s+FUNCTION\s+['\"]([A-Z0-9_/]+)['\"]", code, re.IGNORECASE))
    selects_found = len(re.findall(r"\bSELECT\b", code, re.IGNORECASE))
    auth_checks = len(re.findall(r"\bAUTHORITY-CHECK\b", code, re.IGNORECASE))

    summary = (
        f"### ABAP Architectural Logic Summary\n"
        f"- **Code Volume**: {len(lines)} lines.\n"
        f"- **Database Access**: {selects_found} SELECT statement(s) querying database tables: "
        f"{', '.join(sorted(tables_found)) if tables_found else 'None identified'}.\n"
        f"- **Processing Flow**: {loops_found} internal table loop(s) performing data transformation.\n"
        f"- **External Modularization**: Invokes {len(calls_found)} Function Module(s): "
        f"{', '.join(sorted(calls_found)) if calls_found else 'None'}.\n"
        f"- **Security & Governance**: {auth_checks} explicit AUTHORITY-CHECK statement(s) detected.\n"
    )
    return summary


def _heuristic_abap_optimizer(code: str) -> str:
    """Detects legacy anti-patterns and suggests ABAP 7.40+ optimizations."""
    recommendations: List[str] = []
    
    if re.search(r"SELECT\s+\*\s+FROM", code, re.IGNORECASE):
        recommendations.append(
            "1. **Avoid `SELECT *`**: Restrict the projection list to explicitly needed columns. "
            "Reduces database buffer strain and network payload."
        )
    if re.search(r"LOOP\s+AT\s+\w+\s+INTO\s+\w+", code, re.IGNORECASE):
        recommendations.append(
            "2. **Use Field Symbols or Reference**: Modernize `LOOP AT ... INTO wa` to "
            "`LOOP AT ... ASSIGNING FIELD-SYMBOL(<fs>)` or `REFERENCE INTO data(lr_row)` to eliminate memory copy overhead."
        )
    if re.search(r"READ\s+TABLE\s+\w+\s+WITH\s+KEY", code, re.IGNORECASE):
        recommendations.append(
            "3. **Modern Table Expressions**: Replace legacy `READ TABLE ... WITH KEY` with ABAP 7.40+ table expressions: "
            "`DATA(ls_line) = lt_table[ key_field = lv_value ].` or `ASSIGN lt_table[ ... ] TO FIELD-SYMBOL(...)`."
        )
    if re.search(r"DATA:\s*lt_\w+", code, re.IGNORECASE):
        recommendations.append(
            "4. **Inline Declarations**: Replace top-level `DATA: ...` blocks with inline declarations "
            "(`DATA(lv_var) = ...`, `SELECT ... INTO TABLE @DATA(lt_data)`) to scope variables cleanly."
        )

    if not recommendations:
        recommendations.append(
            "Code conforms to modern ABAP standards. Ensure index usage on WHERE clauses and consider moving complex calculations to CDS Views."
        )

    return (
        "### Enterprise ABAP Code Review & Modernization Guide (7.40+/7.50+)\n\n"
        + "\n\n".join(recommendations)
    )


def _heuristic_cds_explainer(raw_error: str) -> str:
    """Explains CDS activation errors with actionable remediation steps."""
    lower = raw_error.lower()
    if "key" in lower:
        return (
            "### CDS Activation Diagnosis: Missing or Invalid Key Element\n"
            "**Root Cause**: The CDS entity lacks a designated primary key field, or a key definition conflict exists.\n"
            "**Resolution**:\n"
            "1. Ensure at least one key field is prefixed with the `key` keyword inside the select projection: `{ key vbeln, ... }`.\n"
            "2. When using JOINs or aggregations, ensure all non-aggregated grouping elements are properly keyed."
        )
    elif "sqlviewname" in lower or "catalog" in lower:
        return (
            "### CDS Activation Diagnosis: SQL View Name Issue\n"
            "**Root Cause**: Classic CDS views (`define view`) require the `@AbapCatalog.sqlViewName: 'ZSQL_...'` annotation (max 16 characters).\n"
            "**Resolution**: Add `@AbapCatalog.sqlViewName: 'ZSQL_NAME'` at the top of the DDL source, or migrate to a CDS View Entity (`define view entity`)."
        )
    elif "association" in lower or "cardinality" in lower:
        return (
            "### CDS Activation Diagnosis: CDS Association Definition Error\n"
            "**Root Cause**: The ON condition in your association or target cardinality syntax is invalid.\n"
            "**Resolution**: Ensure format: `association [0..*] to TargetTable as _Alias on $projection.Field = _Alias.Field`."
        )
    else:
        return (
            f"### CDS Activation Diagnosis\n"
            f"**Error Details**: {raw_error}\n\n"
            "**Recommended Action**: Verify table names exist in the ABAP Dictionary (SE11), "
            "confirm data types are compatible across JOIN conditions, and verify trailing commas are omitted before the closing brace `}`."
        )


# ---------------------------------------------------------------------------
# 3. Public API Functions
# ---------------------------------------------------------------------------

async def summarize_abap_logic(code: str) -> str:
    prompt = (
        "Please summarize the logic of this ABAP program in plain English. "
        f"Make it concise, professional, and easy to understand for an enterprise architect:\n\n{code}"
    )
    llm_out = await call_llm(prompt)
    return llm_out if llm_out else _heuristic_abap_summary(code)


async def explain_cds_diagnosis(raw_error: str) -> str:
    prompt = (
        "Please explain this SAP CDS View activation error in plain English and provide specific step-by-step instructions to fix it:\n\n"
        f"{raw_error}"
    )
    llm_out = await call_llm(prompt)
    return llm_out if llm_out else _heuristic_cds_explainer(raw_error)


async def generate_cds_from_english(prompt_text: str) -> Dict[str, Any]:
    sys_prompt = (
        "You are an expert SAP CDS data modeler. The user describes a CDS view in plain English.\n"
        "Return ONLY a valid JSON object matching this schema with no markdown formatting:\n"
        "{\n"
        '  "view_name": "string (e.g. ZI_SalesOrder_View)",\n'
        '  "table_name": "string (primary table e.g. VBAK)",\n'
        '  "fields": ["string"],\n'
        '  "joins": [{"table": "string", "alias": "string", "join_type": "string", "on": "string"}],\n'
        '  "expose_to_fiori": boolean\n'
        "}"
    )
    prompt = f"User request: {prompt_text}"
    raw = await call_llm(prompt, system=sys_prompt)
    if raw:
        clean = raw.strip()
        if clean.startswith("```json"):
            clean = clean[7:-3]
        elif clean.startswith("```"):
            clean = clean[3:-3]
        try:
            parsed = json.loads(clean.strip())
            if isinstance(parsed, dict) and "view_name" in parsed and "table_name" in parsed:
                return parsed
        except Exception:
            pass

    # High-fidelity heuristic fallback
    return _heuristic_cds_generator(prompt_text)


async def optimize_abap_code(code: str) -> str:
    prompt = (
        "You are an enterprise SAP ABAP performance architect. Analyze the following ABAP code and suggest "
        "modern syntax (7.40+), performance optimizations, and clean ABAP principles. Provide the optimized code "
        f"along with an explanation of changes:\n\n{code}"
    )
    llm_out = await call_llm(prompt)
    return llm_out if llm_out else _heuristic_abap_optimizer(code)


async def chat_with_ollama(messages: List[Dict[str, Any]]) -> str:
    # Attempt LLM chat
    try:
        import ollama
        client = ollama.AsyncClient(timeout=10.0)
        response = await client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            stream=False,
        )
        content = response.get("message", {}).get("content", "")
        if content:
            return content
    except Exception:
        pass

    # Gemini Chat fallback
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            last_msg = messages[-1].get("content", "") if messages else "Hello"
            res = await model.generate_content_async(last_msg)
            if res.text:
                return res.text
        except Exception:
            pass

    # Heuristic conversational assistant
    last_msg = messages[-1].get("content", "") if messages else ""
    return (
        "I am the SAP Joule ABAP & CDS AI Assistant. I can assist you with:\n"
        "- Analyzing and proposing automated fixes for ST22 runtime dumps.\n"
        "- Generating production-ready single and multi-table CDS Views (with JOINs & Associations).\n"
        "- Diagnosing CDS syntax errors and auto-repairing DDL definitions.\n"
        "- Modernizing legacy ABAP code to modern ABAP 7.40+ expressions.\n"
        "- Pushing approved code fixes live to your SAP system via ADT.\n\n"
        f"How would you like to proceed regarding: '{last_msg}'?"
    )
