"""Point-in-county checks against the 47 Kenya ADM1 county boundaries.

Boundary source: geoBoundaries KEN ADM1 simplified GeoJSON, sourced from
RCMRD GeoPortal / Africa GeoPortal (public-domain boundary, 2020 vintage).
https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM1/
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


_BOUNDARIES_PATH = Path(__file__).resolve().parent / "data" / "kenya_counties.geojson"


def normalize_county(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\s+county$", "", value.strip().lower()))


@lru_cache(maxsize=1)
def _county_features() -> dict[str, dict[str, Any]]:
    with _BOUNDARIES_PATH.open(encoding="utf-8") as source:
        data = json.load(source)
    return {
        normalize_county(feature.get("properties", {}).get("shapeName", "")): feature
        for feature in data.get("features", [])
        if feature.get("properties", {}).get("shapeName")
    }


def _on_segment(point: tuple[float, float], start: list[float], end: list[float]) -> bool:
    px, py = point
    x1, y1 = start[:2]
    x2, y2 = end[:2]
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > 1e-9:
        return False
    return (min(x1, x2) - 1e-9 <= px <= max(x1, x2) + 1e-9
            and min(y1, y2) - 1e-9 <= py <= max(y1, y2) + 1e-9)


def _point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    previous = ring[-1]
    for current in ring:
        if _on_segment(point, previous, current):
            return True
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        if (y1 > y) != (y2 > y):
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def _point_in_polygon(point: tuple[float, float], rings: list[list[list[float]]]) -> bool:
    if not rings or not _point_in_ring(point, rings[0]):
        return False
    return not any(_point_in_ring(point, hole) for hole in rings[1:])


def point_is_in_county(latitude: float, longitude: float, county: str) -> bool:
    """Return whether WGS84 coordinates are inside the selected county polygon."""
    feature = _county_features().get(normalize_county(county))
    if not feature:
        return False

    point = (longitude, latitude)
    geometry = feature.get("geometry") or {}
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    if geometry_type == "Polygon":
        return _point_in_polygon(point, coordinates)
    if geometry_type == "MultiPolygon":
        return any(_point_in_polygon(point, polygon) for polygon in coordinates)
    return False


def county_for_point(latitude: float, longitude: float) -> str | None:
    """Return the county containing a WGS84 point, without returning coordinates."""
    point = (longitude, latitude)
    for feature in _county_features().values():
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates") or []
        if geometry_type == "Polygon":
            inside = _point_in_polygon(point, coordinates)
        elif geometry_type == "MultiPolygon":
            inside = any(_point_in_polygon(point, polygon) for polygon in coordinates)
        else:
            inside = False
        if inside:
            return feature.get("properties", {}).get("shapeName")
    return None
