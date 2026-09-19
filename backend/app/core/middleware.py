import time
import uuid
import logging
import threading
from typing import Dict, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("app.middleware")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects enterprise-standard HTTP response headers to defend against
    MIME-sniffing, clickjacking, cross-site scripting, and downgrade attacks.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Injects and tracks X-Request-ID and measures request duration (X-Process-Time-Ms)
    for high observability, distributed debugging, and latency tracking.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Honor client-provided request ID or issue a new UUIDv4
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Attach request ID to request state for access in endpoint handlers
        request.state.request_id = request_id
        
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Thread-safe in-memory sliding-window rate limiter per client IP.
    Prevents API denial of service and resource exhaustion.
    """
    def __init__(self, app, requests_per_minute: int = 120, burst_limit: Optional[int] = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit or requests_per_minute
        self._history: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def set_limit(self, requests_per_minute: int) -> None:
        with self._lock:
            self.requests_per_minute = requests_per_minute
            self.burst_limit = requests_per_minute

    def reset(self) -> None:
        with self._lock:
            self._history.clear()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exclude CORS preflight OPTIONS requests from consuming rate limit quota
        if request.method == "OPTIONS":
            return await call_next(request)

        # Exclude internal health and OpenAPI documentation from rate limiting
        path = request.url.path
        if path in (
            "/health", 
            "/", 
            "/docs", 
            "/redoc", 
            "/openapi.json", 
            "/api/v1/docs", 
            "/api/v1/redoc", 
            "/api/v1/openapi.json"
        ):
            return await call_next(request)

        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        now = time.time()
        window_start = now - 60.0

        with self._lock:
            # Periodic cleanup to prevent memory exhaustion with high IP volume
            if len(self._history) > 1000:
                stale_keys = [k for k, ts in self._history.items() if not ts or ts[-1] <= window_start]
                for k in stale_keys:
                    del self._history[k]

            timestamps = self._history.get(client_ip, [])
            # Purge entries outside 60-second window
            valid_timestamps = [t for t in timestamps if t > window_start]
            
            if len(valid_timestamps) >= self.burst_limit:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on {path} ({len(valid_timestamps)} reqs/min)")
                retry_after = int(valid_timestamps[0] + 60.0 - now) + 1
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "limit": self.requests_per_minute,
                        "retry_after_seconds": max(retry_after, 1)
                    },
                    headers={
                        "Retry-After": str(max(retry_after, 1)),
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0"
                    }
                )
                
            valid_timestamps.append(now)
            self._history[client_ip] = valid_timestamps
            remaining = max(0, self.burst_limit - len(valid_timestamps))

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
