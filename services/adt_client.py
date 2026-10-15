"""
services/adt_client.py
----------------------
SAP S/4HANA & NetWeaver ABAP Development Tools (ADT) HTTP Client.
Handles connection pooling, CSRF token caching, authentication, and HTTP retries.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote, unquote

import httpx
from config.settings import settings
from core.logger import logger
from btp_proxy import get_sap_client


class SAPADTClient:
    """Async client for SAP ADT REST endpoints."""

    def __init__(self):
        self.base_url = settings.sap_base_url.rstrip("/")
        self.client_id = settings.sap_client
        self.username = settings.sap_username
        self.password = settings.sap_password
        self.verify_ssl = settings.sap_verify_ssl
        self.mock_mode = settings.sap_mock_mode
        self._cached_csrf_token: Optional[str] = None

    async def get_http_client(self) -> httpx.AsyncClient:
        """Retrieves configured HTTP client (with BTP proxy support if on SAP BTP)."""
        return await get_sap_client()

    async def fetch_csrf_token(self, client: Optional[httpx.AsyncClient] = None) -> Tuple[str, str]:
        """Fetches and caches CSRF token from ADT discovery endpoint."""
        if self._cached_csrf_token:
            return self._cached_csrf_token, ""

        if self.mock_mode:
            self._cached_csrf_token = "MOCK_CSRF_TOKEN_2026_S4HANA"
            return self._cached_csrf_token, ""

        url = f"{self.base_url}/sap/bc/adt/discovery"
        headers = {"X-CSRF-Token": "Fetch", "Accept": "application/atomsvc+xml, application/xml"}

        owns_client = False
        if client is None:
            client = await self.get_http_client()
            owns_client = True

        try:
            resp = await client.get(url, auth=(self.username, self.password), headers=headers)
            token = resp.headers.get("X-CSRF-Token", "")
            if not token:
                token = resp.headers.get("x-csrf-token", "")
            if not token:
                raise RuntimeError(f"SAP system did not return a CSRF token (HTTP {resp.status_code})")
            self._cached_csrf_token = token
            return token, resp.text
        finally:
            if owns_client:
                await client.aclose()

    async def sap_get(self, path: str, accept: str = "application/xml") -> httpx.Response:
        """Executes an authenticated GET request against SAP ADT."""
        if self.mock_mode:
            raise RuntimeError(f"Mock mode enabled: direct HTTP network calls to '{path}' are blocked.")

        url = f"{self.base_url}{path}"
        headers = {"Accept": accept}
        client = await self.get_http_client()
        async with client:
            resp = await client.get(url, auth=(self.username, self.password), headers=headers)
            resp.raise_for_status()
            return resp

    async def sap_post(self, path: str, content: str, content_type: str = "application/xml") -> httpx.Response:
        """Executes an authenticated POST request with CSRF protection."""
        if self.mock_mode:
            raise RuntimeError(f"Mock mode enabled: direct HTTP network calls to '{path}' are blocked.")

        client = await self.get_http_client()
        async with client:
            csrf_token, _ = await self.fetch_csrf_token(client)
            url = f"{self.base_url}{path}"
            headers = {
                "Content-Type": content_type,
                "X-CSRF-Token": csrf_token,
            }
            resp = await client.post(url, auth=(self.username, self.password), headers=headers, content=content)
            resp.raise_for_status()
            return resp


adt_client = SAPADTClient()
