"""Shared server-side identity and county checks for public submissions."""

import math
import re
from datetime import date

from fastapi import HTTPException, status

from backend.api.core.kenya_counties import canonical_county_name, county_for_point


def validate_voter_details(
    *,
    voter_name: str | None,
    voter_id_number: str | None,
    county: str | None,
    dob: str | None,
    latitude: float | None,
    longitude: float | None,
    accuracy: float | None,
) -> tuple[str, str, str, bool]:
    """Validate identity/location and report whether county lookup was conclusive."""
    name = (voter_name or "").strip()
    if len(name) < 3 or len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: enter your full name (3–100 characters).",
        )

    national_id = (voter_id_number or "").strip()
    if not re.fullmatch(r"[0-9]{5,12}", national_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: National ID must contain 5–12 numbers only.",
        )

    selected_county = canonical_county_name((county or "").strip())
    if not selected_county:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: select a valid county in Kenya.",
        )

    birth_date_text = (dob or "").strip()
    try:
        birth_date = date.fromisoformat(birth_date_text)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: enter a valid date of birth.",
        )
    today = date.today()
    if birth_date > today:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: date of birth cannot be in the future.",
        )
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if age < 18:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: you must be at least 18 years old.",
        )

    if latitude is None or longitude is None or accuracy is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: allow precise device location and try again.",
        )
    if not all(math.isfinite(value) for value in (latitude, longitude, accuracy)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: device location is invalid.",
        )
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: device coordinates are outside valid ranges.",
        )
    if accuracy <= 0 or accuracy > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: device location must be precise (within 500 metres).",
        )
    detected_county = county_for_point(latitude, longitude)
    if detected_county:
        # When the boundary lookup succeeds, retain the county established by
        # the device coordinates, even if the voter selected a different one.
        return name, national_id, detected_county, True

    # Keep a ballot from being lost solely because the device point is outside
    # Kenya or simplified county polygons omit it. Store the actual device
    # coordinates and accuracy, and mark the selected county as unclassified.
    return name, national_id, selected_county, False
