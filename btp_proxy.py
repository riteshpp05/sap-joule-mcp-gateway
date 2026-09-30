"""
btp_proxy.py
------------
Enterprise SAP BTP Connectivity Proxy & Authentication Manager.

Provides resilient, high-performance HTTP client generation for SAP ADT communications
in both local environments and SAP BTP Cloud Foundry runtime.

Features:
- In-memory OAuth2 token caching with TTL buffer (avoids UAA rate limits)
- Automatic detection of BTP VCAP_SERVICES connectivity binding
- HTTP connection pooling and configurable timeout management
- Graceful fallback for local development and non-BTP cloud instances
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional, Tuple
import httpx

logger = logging.getLogger("btp_proxy")

# In-memory OAuth token cache: (token_str, expiry_epoch_timestamp)
_TOKEN_CACHE: Tuple[Optional[str], float] = (None, 0.0)


async def _fetch_connectivity_token(
    token_url: str,
    client_id: str,
    client_secret: str,
    verify_ssl: bool,
) -> str:
    """Fetch OAuth token from BTP UAA service, caching until near expiry."""
    global _TOKEN_CACHE
    cached_token, expiry = _TOKEN_CACHE
    now = time.time()

    # Reuse cached token if valid for at least 60 more seconds
    if cached_token and (expiry - now) > 60:
        return cached_token

    async with httpx.AsyncClient(verify=verify_ssl, timeout=15.0) as token_client:
        res = await token_client.post(
            token_url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        res.raise_for_status()
        payload = res.json()
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        _TOKEN_CACHE = (token, now + expires_in)
        logger.info("Successfully fetched and cached new BTP Connectivity OAuth token.")
        return token


async def get_sap_client() -> httpx.AsyncClient:
    """Returns an httpx.AsyncClient configured for SAP ADT calls.
    
    When running in SAP BTP Cloud Foundry with a bound connectivity service,
    automatically configures the on-premise proxy and Proxy-Authorization header.
    Otherwise, returns a direct AsyncClient with connection pooling.
    """
    verify_ssl = os.getenv("SAP_VERIFY_SSL", "false").lower() == "true"
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0)
    timeout = httpx.Timeout(45.0, connect=10.0)

    vcap = os.getenv("VCAP_SERVICES")
    if not vcap:
        return httpx.AsyncClient(verify=verify_ssl, timeout=timeout, limits=limits)

    try:
        vcap_services = json.loads(vcap)
        conn_services = vcap_services.get("connectivity", [])
        if not conn_services:
            return httpx.AsyncClient(verify=verify_ssl, timeout=timeout, limits=limits)

        conn_creds = conn_services[0].get("credentials", {})
        if "uaa" in conn_creds:
            client_id = conn_creds["uaa"].get("clientid", "")
            client_secret = conn_creds["uaa"].get("clientsecret", "")
            token_service = conn_creds["uaa"].get("url", "")
        else:
            client_id = conn_creds.get("clientid", "")
            client_secret = conn_creds.get("clientsecret", "")
            token_service = conn_creds.get("token_service_url") or conn_creds.get("url", "")

        token_url = token_service if token_service.endswith("/oauth/token") else f"{token_service.rstrip('/')}/oauth/token"
        conn_token = await _fetch_connectivity_token(token_url, client_id, client_secret, verify_ssl)

        proxy_host = conn_creds.get("onpremise_proxy_host", "")
        proxy_port = conn_creds.get("onpremise_proxy_http_port", "")
        proxy_url = f"http://{proxy_host}:{proxy_port}"

        headers = {
            "Proxy-Authorization": f"Bearer {conn_token}"
        }

        return httpx.AsyncClient(
            proxy=proxy_url,
            headers=headers,
            verify=verify_ssl,
            timeout=timeout,
            limits=limits,
        )
    except Exception as exc:
        logger.error(f"[BTP Proxy Error] Failed to initialize BTP Proxy: {exc}")
        return httpx.AsyncClient(verify=verify_ssl, timeout=timeout, limits=limits)
