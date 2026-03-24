# ---------------------------------------------------------------------------
# Global exception handlers for FastAPI
# ---------------------------------------------------------------------------
# Attach to the app instance via ``register_exception_handlers(app)``.
# Catches unhandled errors and returns a consistent JSON shape.
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Wire up global exception handlers on *app*."""

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "detail": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = " → ".join(str(l) for l in err.get("loc", []))
            errors.append({"field": loc, "message": err.get("msg", "")})
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "detail": {"error": "Validation failed", "fields": errors},
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            exc,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": {"error": "Internal server error"},
            },
        )
