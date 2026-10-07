import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

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

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean expired timestamps
        timestamps = self.request_counts[client_ip]
        self.request_counts[client_ip] = [ts for ts in timestamps if now - ts < self.window_seconds]

        if len(self.request_counts[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Velocity rate limit exceeded. Please wait before casting additional ballots."
            )

        self.request_counts[client_ip].append(now)
        response = await call_next(request)
        return response
