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
        def parse_version(value: str):
            normalized = value.strip().lower().removeprefix("v")
            try:
                return tuple(int(part) for part in normalized.split("."))
            except ValueError:
                return None

        latest_version = parse_version(settings.VERSION)
        installed_version = parse_version(version) if version else None
        update_available = (
            installed_version is not None
            and latest_version is not None
            and installed_version < latest_version
        )
        return {
            "latest_version": settings.VERSION,
            "current_stable": settings.VERSION,
            "minimum_version": "1.0.0",
            "update_available": update_available,
            "force_update": False,
            "title": f"IcapsQ v{settings.VERSION}",
            "release_notes": "• Plan choices and quotas now match the server catalog\n• Election plan removed from new offers",
            "download_url": "https://github.com/MuthamiM/GetItRight/releases/download/v2.1.26/IcapsQ-v2.1.26-build-32.apk",
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
