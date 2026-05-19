"""
Request-Logging-Middleware: setzt trace_id pro Request (Observability).
"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.logging import trace_id_var, get_logger

log = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())[:8]
        trace_id_var.set(trace_id)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        log.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)",
            extra={"trace_id": trace_id},
        )
        response.headers["X-Trace-Id"] = trace_id
        return response
