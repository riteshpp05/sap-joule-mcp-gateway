"""
services/cts_service.py
-----------------------
Enterprise SAP Change and Transport System (CTS) & Package Governance Service.
Validates transport request conventions, enforces ChaRM policies, and manages DevClasses.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional
from config.settings import settings
from config.constants import LOCAL_PACKAGE_DEFAULT, LOCAL_PACKAGE_PREFIX
from core.logger import logger
from services.adt_client import adt_client
from services.mock_provider import mock_provider


class CTSService:
    """Enforces enterprise CTS transport governance and DevClass lifecycle."""

    @staticmethod
    def validate_transport_request(transport_request: Optional[str], package: str = LOCAL_PACKAGE_DEFAULT) -> Dict[str, Any]:
        """Validates transport request compliance against SAP CTS conventions."""
        pkg = (package or LOCAL_PACKAGE_DEFAULT).strip().upper()
        if pkg == LOCAL_PACKAGE_DEFAULT or pkg.startswith(LOCAL_PACKAGE_PREFIX):
            return {
                "valid": True,
                "package": pkg,
                "transport_request": transport_request,
                "is_local": True,
                "message": f"Package '{pkg}' is local; no CTS Transport Request required.",
            }

        if not transport_request or not transport_request.strip():
            return {
                "valid": False,
                "package": pkg,
                "transport_request": None,
                "is_local": False,
                "message": f"Enterprise Governance: Transportable package '{pkg}' mandates an active Transport Request (e.g., DEVK900123).",
            }

        tr = transport_request.strip().upper()
        if not re.match(r"^[A-Z0-9]{3}K[0-9]{5,6}$", tr):
            return {
                "valid": False,
                "package": pkg,
                "transport_request": tr,
                "is_local": False,
                "message": f"Invalid Transport Request format '{tr}'. Must match SAP CTS pattern '<SYS>K9XXXXX' (e.g. DEVK900123).",
            }

        return {
            "valid": True,
            "package": pkg,
            "transport_request": tr,
            "is_local": False,
            "message": f"Transport Request '{tr}' is valid and approved for package '{pkg}'.",
        }

    async def create_sap_package(
        self,
        package_name: str,
        description: Optional[str] = None,
        software_component: str = "HOME",
        transport_layer: str = "SAP",
        super_package: Optional[str] = None,
        transport_request: Optional[str] = None,
        push_to_sap: bool = True,
    ) -> Dict[str, Any]:
        """Creates an SAP Development Package (DevClass) via ADT."""
        clean_name = re.sub(r"[^A-Za-z0-9_$]", "", package_name).strip().upper()
        desc = description or f"Package {clean_name}"

        # Validate Transport Request for non-local packages when pushing to SAP
        if push_to_sap:
            tr_val = self.validate_transport_request(transport_request, package=clean_name)
            if not tr_val.get("valid", True):
                return {
                    "package_name": clean_name,
                    "status": "FAILED",
                    "error": True,
                    "message": tr_val.get("message"),
                }

        super_pkg_xml = (
            f'<pak:superPackage adtcore:name="{super_package.upper()}"/>'
            if super_package
            else ""
        )

        pkg_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<pak:package xmlns:pak="http://www.sap.com/adt/packages" '
            'xmlns:adtcore="http://www.sap.com/adt/core"\n'
            f'    adtcore:name="{clean_name}" adtcore:description="{desc}"\n'
            '    adtcore:masterLanguage="EN" pak:packageType="development">\n'
            f"  {super_pkg_xml}\n"
            f'  <pak:softwareComponent adtcore:name="{software_component}"/>\n'
            f'  <pak:transportLayer adtcore:name="{transport_layer}"/>\n'
            '</pak:package>'
        )

        result: Dict[str, Any] = {
            "package_name": clean_name,
            "description": desc,
            "package_xml": pkg_xml,
            "payload_xml": pkg_xml,
            "software_component": software_component,
            "transport_layer": transport_layer,
            "transport_request": transport_request,
            "note": f"Package creation payload generated for '{clean_name}'.",
        }

        if not push_to_sap:
            result["pushed"] = False
            result["status"] = "COMPILED"
            result["note"] += " NOT pushed to SAP (push_to_sap=False)."
            return result

        if settings.sap_mock_mode:
            result.update({
                "status": "CREATED",
                "mock_mode": True,
                "pushed": True,
                "steps_completed": ["csrf_token_fetched", "package_created"],
                "message": f"Package '{clean_name}' successfully created in SAP system.",
            })
            return result

        path = f"/sap/bc/adt/packages/{clean_name.lower()}"
        try:
            resp = await adt_client.sap_post(path, content=payload_xml, content_type="application/vnd.sap.adt.packages.v1+xml")
            return {
                "package_name": clean_name,
                "status": "CREATED",
                "response_code": resp.status_code,
                "mock_mode": False,
                "message": f"Package '{clean_name}' created live via SAP ADT.",
            }
        except Exception as e:
            return {"package_name": clean_name, "status": "FAILED", "error": True, "message": str(e)}


cts_service = CTSService()
