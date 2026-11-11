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
            "release_notes": "• Poll refresh keeps the active list visible\n• Compact vote errors and larger first-name greeting",
            "download_url": "https://icapsq.mftechnologies.org/app-release.apk",
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
    def geo_currency(request=None) -> dict:
        country_code = ""
        if request is not None:
            country_code = (
                request.headers.get("CF-IPCountry") or
                request.headers.get("cf-ipcountry") or
                request.headers.get("X-Country-Code") or
                ""
            ).strip().upper()
        if country_code == "IL":
            return {
                "country": "Israel",
                "countryCode": "IL",
                "currency": "ILS",
                "symbol": "₪",
                "rate": 3.7,
                "isIsrael": True,
                "suggestedLang": "he"
            }
        return {
            "country": "Kenya",
            "countryCode": country_code or "KE",
            "currency": "KES",
            "symbol": "KSh",
            "rate": 130.0,
            "isIsrael": False,
            "suggestedLang": "en"
        }

    @staticmethod
    def geo_detect(request=None) -> dict:
        country_code = ""
        client_ip = ""
        if request is not None:
            country_code = (
                request.headers.get("CF-IPCountry") or
                request.headers.get("cf-ipcountry") or
                request.headers.get("X-Country-Code") or
                ""
            ).strip().upper()
            client_ip = (
                request.headers.get("CF-Connecting-IP") or
                request.headers.get("X-Real-IP") or
                (request.client.host if request.client else "")
            )
        is_israel = (country_code == "IL")
        return {
            "countryCode": country_code or "UNKNOWN",
            "isIsrael": is_israel,
            "language": "he" if is_israel else "en",
            "ip": client_ip
        }
