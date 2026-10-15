"""
config/constants.py
-------------------
Standardized enterprise constants, enums, and HTTP header definitions.
"""

from enum import Enum


class TransportStatus(str, Enum):
    MODIFIABLE = "D"
    RELEASED = "R"


class ViewType(str, Enum):
    ENTITY = "entity"
    CLASSIC = "classic"


class FixProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUSHED = "PUSHED"


class UnitTestStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"


# Standard Headers
HEADER_CORRELATION_ID = "X-Correlation-ID"
HEADER_REQUEST_ID = "X-Request-ID"
HEADER_RESPONSE_TIME = "X-Response-Time"
HEADER_API_KEY = "X-API-Key"
HEADER_CSRF_TOKEN = "X-CSRF-Token"

# Default Local Package
LOCAL_PACKAGE_PREFIX = "$"
LOCAL_PACKAGE_DEFAULT = "$TMP"
