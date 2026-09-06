"""Request-ID correlation middleware.

Generates a unique ``X-Request-ID`` header for every inbound request (or
reuses one supplied by the caller) and binds it into the structlog context
so that **all** log lines emitted during that request carry the same ID.

The ID is also echoed back in the response headers for easy client-side
tracing.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Injects a per-request correlation ID into logs and response headers."""

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        # Honour an externally-provided ID (e.g. from an API gateway) or mint a new one.
        request_id = request.headers.get(_HEADER) or str(uuid.uuid4())

        # Bind into structlog contextvars so every logger.info/error/… in this
        # request's call-chain automatically includes ``request_id``.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers[_HEADER] = request_id
        return response


__all__ = ["RequestIdMiddleware"]
