import logging
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("getitright.middleware.error")

class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """Catches unhandled server errors and returns consistent, resilient JSON payloads."""
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"[SERVER ERROR] {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred. Telemetry recorded for cryptographic audit.",
                    "error": str(exc),
                    "path": request.url.path
                }
            )
