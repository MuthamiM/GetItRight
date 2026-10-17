import time
from collections import defaultdict
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class InMemoryRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 300, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exempt health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        client_ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "127.0.0.1")
        # Exempt local development and loopback requests to avoid developer lockout
        if client_ip in ["127.0.0.1", "::1", "localhost", "testclient"]:
            return await call_next(request)

        now = time.time()

        path = request.url.path
        if path.endswith("/auth/login"):
            max_requests, window_seconds = 5, 15 * 60
        elif path.endswith("/auth/register"):
            max_requests, window_seconds = 5, 60 * 60
        elif path.endswith("/vote") or path.endswith("/respond") or path.endswith("/submit"):
            max_requests, window_seconds = 20, 60
        else:
            max_requests, window_seconds = self.max_requests, self.window_seconds
        
        key = f"{client_ip}:{path}"
        timestamps = self.request_counts[key]
        timestamps = [ts for ts in timestamps if now - ts < window_seconds]
        self.request_counts[key] = timestamps

        if len(timestamps) >= max_requests:
            retry_after = max(1, int(window_seconds - (now - min(timestamps))))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please wait before trying again."},
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        # Successful authentication must not consume the failed-login budget.
        # This keeps the limit useful for credential attacks without locking
        # out valid admin and client users sharing one IP address.
        if path.endswith("/auth/login") and response.status_code in {401, 403}:
            self.request_counts[key].append(now)
        return response
