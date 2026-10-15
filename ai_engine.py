"""
ai_engine.py
------------
Enterprise Facade for AI Intelligence Services.
Delegates to services.ai_service for multi-provider LLM orchestration:
- Summarize ABAP architecture
- Clean ABAP 7.40+ performance optimization
- CDS checkrun error diagnosis
- Natural language English-to-CDS compilation
- Conversational Copilot assistant
"""

from __future__ import annotations

from typing import Any, Dict, List
from services.ai_service import ai_service


async def summarize_abap_logic(code: str) -> str:
    """Summarizes ABAP code architecture and business logic."""
    return await ai_service.summarize_abap_logic(code)


async def optimize_abap_code(code: str) -> str:
    """Analyzes ABAP code and suggests Clean ABAP 7.40+ optimizations."""
    return await ai_service.optimize_abap_code(code)


async def explain_cds_diagnosis(raw_error: str) -> str:
    """Explains CDS checkrun activation errors with actionable steps."""
    return await ai_service.explain_cds_diagnosis(raw_error)


async def generate_cds_from_english(prompt_text: str) -> Dict[str, Any]:
    """Generates structured CDS specification from plain English description."""
    return await ai_service.generate_cds_from_english(prompt_text)


async def chat(messages: List[Dict[str, str]]) -> str:
    """Processes conversational questions for Joule assistant."""
    return await ai_service.chat(messages)
