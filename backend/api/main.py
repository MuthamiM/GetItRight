import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.core.config import settings
from backend.api.middleware import (
    InMemoryRateLimiter, TelemetryMiddleware,
    SecurityHeadersMiddleware, GlobalExceptionMiddleware
)
from backend.api.features.auth.routes import router as auth_router
from backend.api.features.polls.routes import router as polls_router
from backend.api.features.surveys.routes import router as surveys_router
from backend.api.features.analytics.routes import router as analytics_router
from backend.api.features.users.routes import router as users_router
from backend.api.features.privacy.routes import router as privacy_router

from backend.api.controllers import SystemController
from backend.api.servers import ws_server, server_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background telemetry & server manager
    await server_manager.start()
    yield
    # Shutdown: Clean background services
    await server_manager.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Unified High-Throughput REST & WebSocket Server for Polling, Surveys, Quotas, and Cryptographic Merkle Verification.",
    lifespan=lifespan
)

# === MIDDLEWARE STACK ===
# 1. Global Exception Handling Middleware
app.add_middleware(GlobalExceptionMiddleware)

# 2. Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# 3. Security Headers & Privacy Boundary
app.add_middleware(SecurityHeadersMiddleware)

# 4. High-Resolution Telemetry & Latency Tracking
app.add_middleware(TelemetryMiddleware)

# 5. Token Bucket Rate Limiting
app.add_middleware(InMemoryRateLimiter, max_requests=600, window_seconds=60)

# === WEBSOCKET SERVERS ===
@app.websocket("/ws/votes")
@app.websocket(f"{settings.API_PREFIX}/ws/votes")
async def websocket_votes(websocket: WebSocket):
    """Real-time live voting broadcast server for mobile and web clients."""
    origin = websocket.headers.get("origin")
    if origin and origin.rstrip("/") not in settings.cors_origins:
        await websocket.close(code=1008)
        return
    await ws_server.connect_vote(websocket)
    try:
        while True:
            # Keepalive / incoming ping handling
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_server.disconnect_vote(websocket)
    except Exception:
        ws_server.disconnect_vote(websocket)

@app.websocket("/ws/telemetry")
@app.websocket(f"{settings.API_PREFIX}/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """Real-time live telemetry streaming server for platform monitoring dashboards."""
    origin = websocket.headers.get("origin")
    if origin and origin.rstrip("/") not in settings.cors_origins:
        await websocket.close(code=1008)
        return
    await ws_server.connect_telemetry(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_server.disconnect_telemetry(websocket)
    except Exception:
        ws_server.disconnect_telemetry(websocket)

# === FEATURE ROUTERS ===
for prefix in [settings.API_PREFIX, "/api/v1"]:
    app.include_router(auth_router, prefix=prefix)
    app.include_router(polls_router, prefix=prefix)
    app.include_router(surveys_router, prefix=prefix)
    app.include_router(analytics_router, prefix=prefix)
    app.include_router(users_router, prefix=prefix)
    app.include_router(privacy_router, prefix=prefix)

# === SYSTEM CONTROLLER DIAGNOSTICS ===
@app.get("/health")
@app.get(f"{settings.API_PREFIX}/health")
def health_check():
    return SystemController.health_check()

@app.get("/app/version")
@app.get(f"{settings.API_PREFIX}/app/version")
def check_app_version(version: str = None):
    return SystemController.app_version(version)

@app.get(f"{settings.API_PREFIX}/cache/status")
def cache_status():
    return SystemController.cache_status()

@app.get(f"{settings.API_PREFIX}/geo/currency")
def geo_currency():
    return SystemController.geo_currency()

# === SERVE FRONTEND STATIC FILES FROM /web ===
WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
if WEB_DIR.exists():
    @app.get("/")
    def serve_landing():
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=5000, reload=True)
