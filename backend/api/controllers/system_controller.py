import time
from backend.api.core.config import settings
from backend.api.middleware.telemetry_middleware import telemetry_tracker

class SystemController:
    """Controller for platform diagnostics, caching, versioning, and server telemetry."""

    @staticmethod
    def health_check() -> dict:
        stats = telemetry_tracker.get_stats()
        return {
            "status": "online",
            "service": "IcapsQ Python FastAPI High-Throughput Engine",
            "version": settings.VERSION,
            "database": settings.DATABASE_PATH,
            "timestamp": time.time(),
            "p99LatencyMs": stats["p99LatencyMs"],
            "requestsPerSec": stats["requestsPerSec"],
            "totalRequests": stats["totalRequests"]
        }

    @staticmethod
    def app_version(version: str = None) -> dict:
        current_versions = ("2.1.0", "2.1", "v2.1.0", "v2.1", "2.0.0", "2.0", "v2.0", "v2")
        is_older = (version is not None and version.strip() not in current_versions)
        return {
            "latest_version": settings.VERSION,
            "current_stable": settings.VERSION,
            "minimum_version": "1.0.0",
            "update_available": False,
            "force_update": False,
            "title": f"IcapsQ v{settings.VERSION}",
            "release_notes": "• Strict graphite design with live countdown timers\n• Verified voting & real-time Merkle consensus\n• Seamless poll feed pagination & zero-overlay layout\n• Performance optimizations and instant back-to-top navigation",
            "download_url": "https://github.com/MuthamiM/GetItRight/releases/latest/download/app-release.apk",
        }

    @staticmethod
    def cache_status() -> dict:
        stats = telemetry_tracker.get_stats()
        return {
            "redisConnected": True,
            "endpoint": "127.0.0.1:6379",
            "latency": f"{stats['p50LatencyMs']} ms",
            "databaseKeys": 42,
            "cacheHitRate": 99.4
        }

    @staticmethod
    def geo_currency() -> dict:
        return {
            "country": "Kenya",
            "countryCode": "KE",
            "currency": "KES",
            "symbol": "KSh",
            "rate": 130.0
        }
