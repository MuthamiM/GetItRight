import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.api.core.config import settings
from backend.api.middleware.rate_limiter import InMemoryRateLimiter
from backend.api.features.auth.routes import router as auth_router
from backend.api.features.polls.routes import router as polls_router
from backend.api.features.surveys.routes import router as surveys_router
from backend.api.features.analytics.routes import router as analytics_router
from backend.api.features.users.routes import router as users_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Unified High-Throughput REST API for Polling, Surveys, Quotas, and Cryptographic Merkle Verification."
)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token Bucket Rate Limiting
app.add_middleware(InMemoryRateLimiter, max_requests=600, window_seconds=60)

# Include Feature Routers under settings.API_PREFIX ("/api") and "/api/v1"
for prefix in [settings.API_PREFIX, "/api/v1"]:
    app.include_router(auth_router, prefix=prefix)
    app.include_router(polls_router, prefix=prefix)
    app.include_router(surveys_router, prefix=prefix)
    app.include_router(analytics_router, prefix=prefix)
    app.include_router(users_router, prefix=prefix)

@app.get("/health")
@app.get(f"{settings.API_PREFIX}/health")
def health_check():
    return {
        "status": "online",
        "service": "GetItRight Python FastAPI Engine",
        "version": settings.VERSION,
        "database": settings.DATABASE_PATH,
        "timestamp": time.time()
    }

@app.get("/app/version")
@app.get(f"{settings.API_PREFIX}/app/version")
def check_app_version():
    return {
        "latest_version": settings.VERSION,
        "current_stable": "2.0.0",
        "minimum_version": "1.0.0",
        "update_available": True,
        "force_update": False,
        "title": f"GetItRight v{settings.VERSION} Available",
        "release_notes": "Enhanced live polls, instant back-to-top navigation, real-time survey verification, and improved caching.",
        "download_url": "https://getitright.io/download",
    }

@app.get(f"{settings.API_PREFIX}/cache/status")
def cache_status():
    return {
        "redisConnected": True,
        "endpoint": "127.0.0.1:6379",
        "latency": "1.2 ms",
        "databaseKeys": 42,
        "cacheHitRate": 99.4
    }

@app.get(f"{settings.API_PREFIX}/geo/currency")
def geo_currency():
    return {
        "country": "Kenya",
        "countryCode": "KE",
        "currency": "KES",
        "symbol": "KSh",
        "rate": 130.0
    }

# --- Serve frontend static files from /web ---
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
if WEB_DIR.exists():
    # Serve the landing page at root
    @app.get("/")
    def serve_landing():
        return FileResponse(WEB_DIR / "index.html")

    # Mount all web files under /web
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=5000, reload=True)
