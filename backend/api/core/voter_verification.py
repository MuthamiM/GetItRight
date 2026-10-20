"""Shared server-side identity and county checks for public submissions."""

import math
import re
from datetime import date

from fastapi import HTTPException, status

from backend.api.core.kenya_counties import county_for_point, point_is_in_county


def validate_voter_details(
    *,
    voter_name: str | None,
    voter_id_number: str | None,
    county: str | None,
    dob: str | None,
    latitude: float | None,
    longitude: float | None,
    accuracy: float | None,
) -> tuple[str, str]:
    """Require complete details and verify the reported GPS point matches county."""
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

    selected_county = (county or "").strip()
    if not selected_county:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: select your county.",
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
    if accuracy <= 0 or accuracy > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide correct details: device location must be precise (within 500 metres).",
        )
    if not point_is_in_county(latitude, longitude, selected_county):
        detected_county = county_for_point(latitude, longitude)
        location_detail = (
            f" Detected location: {detected_county} County. Select the correct county or try again from {selected_county} County."
            if detected_county
            else " Device location must be within the selected county in Kenya."
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Please provide correct details: your device location does not match {selected_county} County.{location_detail}",
        )

    return name, national_id
