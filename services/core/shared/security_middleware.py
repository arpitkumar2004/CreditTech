"""P6 — Security hardening middleware.

Adds:
    * Security headers (X-Content-Type-Options, Referrer-Policy, X-Frame-Options,
      Strict-Transport-Security, Content-Security-Policy for HTML responses).
    * Request-size cap (413 on oversize bodies).
    * Simple in-memory rate limit keyed by client IP (per-minute window).

No auth changes — this is defense-in-depth for the pilot only.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

DEFAULT_MAX_BODY = 1_048_576   # 1 MiB
DEFAULT_RATE_PER_MIN = 240


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        ct = response.headers.get("content-type", "")
        if ct.startswith("text/html"):
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:",
            )
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_bytes: int = DEFAULT_MAX_BODY) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > self.max_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": f"Request body exceeds {self.max_bytes} bytes"},
            )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-process token bucket per client IP. Not clustered — pilot only."""

    def __init__(self, app: ASGIApp, per_minute: int = DEFAULT_RATE_PER_MIN) -> None:
        super().__init__(app)
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Never rate-limit health, and honor a global bypass toggle
        # (used by the test suite where every request shares one client host).
        if request.url.path == "/health" or os.environ.get("DISABLE_RATE_LIMIT") == "1":
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self._hits[client]
        cutoff = now - 60.0
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= self.per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"},
                headers={"Retry-After": "60"},
            )
        window.append(now)
        return await call_next(request)


__all__ = [
    "SecurityHeadersMiddleware", "BodySizeLimitMiddleware", "RateLimitMiddleware",
    "DEFAULT_MAX_BODY", "DEFAULT_RATE_PER_MIN",
]
