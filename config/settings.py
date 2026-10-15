"""
config/settings.py
------------------
Enterprise Configuration Management via Pydantic BaseSettings.
All configuration parameters are dynamically read from the environment or .env file.
Zero hardcoded credentials, hosts, or ports.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    # Application & Server Details
    app_name: str = Field(default="SAP Joule AI Agent & MCP Gateway", description="Application display name")
    app_version: str = Field(default="2.0.0", description="Semantic version")
    host: str = Field(default="127.0.0.1", description="ASGI server binding host")
    port: int = Field(default=8080, description="ASGI server binding port")
    debug: bool = Field(default=False, description="Debug mode toggle")

    # Security & Access Control
    gateway_api_key: str = Field(default="", description="Optional master API key for gateway protection")
    allowed_origins: str = Field(default="*", description="CORS allowed origins (comma-separated or '*')")

    # SAP ADT Integration
    sap_base_url: str = Field(default="https://sap-mock-gateway.internal:44300", description="SAP ADT base URL")
    sap_client: str = Field(default="100", description="SAP Mandant / Client ID")
    sap_username: str = Field(default="MOCK_DEVELOPER", description="SAP ADT service user")
    sap_password: str = Field(default="", description="SAP ADT service password")
    sap_verify_ssl: bool = Field(default=False, description="Verify SSL certificates for ADT HTTPS connections")
    sap_mock_mode: bool = Field(default=True, description="Enforce safe isolated mock mode when True")

    # AI Engine Configuration
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    ollama_model: str = Field(default="qwen2.5:3b", description="Local Ollama model name")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API base URL")

    # Storage & Fixtures
    fixtures_dir: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures"),
        description="Path to mock catalog fixtures",
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.allowed_origins or self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache()
def get_settings() -> AppSettings:
    """Returns singleton cached instance of application settings."""
    return AppSettings()


# Global accessible settings instance
settings = get_settings()
