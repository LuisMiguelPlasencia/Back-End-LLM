# ---------------------------------------------------------------------------
# Standardised HTTP response helpers
# ---------------------------------------------------------------------------
# Gives every endpoint a uniform JSON envelope:
#
#   Success → { "status": "success", "data": ... }
#   Error   → HTTPException with { "detail": { "error": "...", "code": "..." } }
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Success helpers
# ---------------------------------------------------------------------------

def ok(data: Any = None, *, status_code: int = 200, message: str = "success") -> JSONResponse:
    """Return a JSON success envelope."""
    body: dict[str, Any] = {"status": message}
    if data is not None:
        body["data"] = data
    return JSONResponse(content=body, status_code=status_code)


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def error(
    status_code: int,
    message: str,
    *,
    code: Optional[str] = None,
) -> None:
    """Raise an ``HTTPException`` with a structured detail payload.

    Always *raises* — callers do not need ``return`` after calling this.

    Parameters
    ----------
    status_code:
        HTTP status code (4xx / 5xx).
    message:
        Human-readable error description.
    code:
        Optional machine-readable error code (e.g. ``"INVALID_COUPON"``).
    """
    detail: dict[str, str] = {"error": message}
    if code:
        detail["code"] = code
    raise HTTPException(status_code=status_code, detail=detail)
