import base64
import hashlib
import hmac
import json
import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.core.config import settings
from backend.api.core.database import get_db
from backend.api.features.privacy.models import BrowserStorageSnapshotModel, GoogleProfileConsentModel
from backend.api.middleware.auth_middleware import get_optional_current_user_token, require_admin


router = APIRouter(prefix="/privacy", tags=["Privacy & Browser Storage"])

CATEGORY_FIELDS = {
    "account": {"id", "fullName", "email", "phoneNumber", "role", "organization"},
    "voter_identity": {"name", "nationalId"},
    "demographics": {"county", "dateOfBirth", "verificationComplete", "verified"},
    "location": {"latitude", "longitude", "accuracy", "capturedAt"},
    "device": {"model", "platform", "userAgent", "language", "screen", "cookieEnabled"},
    "activity": {"assignedId", "voterKey", "surveySessionId", "completedPollIds", "completedSurveyIds", "lastSurveyOpened"},
    "preferences": {"language", "cookiePreference", "analytics", "adminReview"},
    "drafts": {"items"},
    "browser_storage": {"cookieNames", "sessionKeys"},
    "notifications": {"notificationReadKeys"},
}


def _cipher() -> Fernet:
    key = base64.urlsafe_b64encode(
        hashlib.sha256(("icapsq-browser-storage:" + settings.SECRET_KEY).encode("utf-8")).digest()
    )
    return Fernet(key)


def _clean_value(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return None
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        return value.strip()[:2000]
    if isinstance(value, list):
        return [_clean_value(item, depth + 1) for item in value[:60]]
    if isinstance(value, dict):
        cleaned = {}
        for key, item in list(value.items())[:80]:
            safe_key = str(key)[:80]
            if re.search(r"token|password|secret|authorization|credential|cookie.?value", safe_key, re.I):
                continue
            cleaned[safe_key] = _clean_value(item, depth + 1)
        return cleaned
    return str(value)[:500]


def _without_exact_coordinates(value: Any) -> Any:
    """Hide exact GPS values in admin snapshots while retaining DB records."""
    coordinate_keys = {"latitude", "longitude", "lat", "lng", "coordinates", "gpscoordinates"}
    if isinstance(value, list):
        return [_without_exact_coordinates(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _without_exact_coordinates(item)
            for key, item in value.items()
            if re.sub(r"[^a-z]", "", str(key).lower()) not in coordinate_keys
        }
    return value


class BrowserStorageSnapshotIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    browser_id: str = Field(alias="browserId", min_length=20, max_length=80)
    collection_enabled: bool = Field(alias="collectionEnabled")
    consent_version: int = Field(alias="consentVersion", ge=2)
    source_path: str = Field(alias="sourcePath", default="", max_length=180)
    categories: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("browser_id")
    @classmethod
    def validate_browser_id(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{20,80}", value):
            raise ValueError("browserId must be a random browser identifier")
        return value

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, value: str) -> str:
        clean = value.strip()
        if clean and (not clean.startswith("/") or clean.startswith("//")):
            raise ValueError("sourcePath must be a relative path")
        return clean

    @model_validator(mode="after")
    def validate_categories(self):
        unknown = set(self.categories) - set(CATEGORY_FIELDS)
        if unknown:
            raise ValueError("Unknown browser data category")
        serialized = json.dumps(self.categories, ensure_ascii=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > 64 * 1024:
            raise ValueError("Browser data snapshot exceeds 64 KB")
        return self


class GoogleProfileConsentIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    credential: str = Field(min_length=100, max_length=8192)
    consent: bool
    source_path: str = Field(alias="sourcePath", default="", max_length=180)

    @field_validator("consent")
    @classmethod
    def require_consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Google profile sharing consent is required")
        return value

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, value: str) -> str:
        clean = value.strip()
        if clean and (not clean.startswith("/") or clean.startswith("//")):
            raise ValueError("sourcePath must be a relative path")
        return clean


@router.get("/google-profile/config")
def google_profile_config():
    """Return the public Google web client ID needed to show explicit consent UI."""
    return {
        "enabled": bool(settings.GOOGLE_OAUTH_CLIENT_ID),
        "clientId": settings.GOOGLE_OAUTH_CLIENT_ID,
        "scopes": ["openid", "email", "profile"],
    }


@router.post("/google-profile", status_code=status.HTTP_202_ACCEPTED)
def save_google_profile(
    payload: GoogleProfileConsentIn,
    db: Session = Depends(get_db),
):
    """Verify a user-approved Google ID token and save only the basic OIDC profile."""
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google profile sharing is not configured")

    try:
        from google.auth.exceptions import GoogleAuthError
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            payload.credential,
            GoogleRequest(),
            audience=settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google sign-in could not be verified")
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google verification is temporarily unavailable")

    subject = claims.get("sub")
    email = claims.get("email")
    if not subject or not email or claims.get("aud") != settings.GOOGLE_OAUTH_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google sign-in did not return a valid account profile")

    now = datetime.now(timezone.utc).isoformat()
    profile = {
        "googleAccountId": str(subject),
        "name": claims.get("name"),
        "givenName": claims.get("given_name"),
        "familyName": claims.get("family_name"),
        "email": str(email),
        "emailVerified": claims.get("email_verified") is True,
        "profilePicture": claims.get("picture"),
        "locale": claims.get("locale"),
        "scopes": ["openid", "email", "profile"],
        "consentVersion": 1,
        "consentAt": now,
    }
    profile = {key: value for key, value in profile.items() if value is not None}
    subject_hash = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        ("google-profile:" + str(subject)).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    encrypted = _cipher().encrypt(
        json.dumps(profile, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")

    row = db.query(GoogleProfileConsentModel).filter(
        GoogleProfileConsentModel.GoogleSubjectHash == subject_hash
    ).first()
    if row:
        row.EncryptedJson = encrypted
        row.CapturedAt = now
        row.SourcePath = payload.source_path
    else:
        db.add(GoogleProfileConsentModel(
            GoogleSubjectHash=subject_hash,
            EncryptedJson=encrypted,
            CapturedAt=now,
            SourcePath=payload.source_path,
        ))
    db.commit()
    return {"saved": True, "capturedAt": now, "storedFields": sorted(profile.keys())}


@router.post("/browser-storage", status_code=status.HTTP_202_ACCEPTED)
def save_browser_storage_snapshot(
    payload: BrowserStorageSnapshotIn,
    current_user: Optional[dict] = Depends(get_optional_current_user_token),
    db: Session = Depends(get_db),
):
    """Save explicitly consented, allow-listed browser data for admin fraud review."""
    if not payload.collection_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Browser data collection consent is required")

    now = datetime.now(timezone.utc).isoformat()
    cipher = _cipher()
    saved = 0

    try:
        for category, allowed_fields in CATEGORY_FIELDS.items():
            raw_category = payload.categories.get(category, {})
            cleaned = {
                key: _clean_value(value)
                for key, value in raw_category.items()
                if key in allowed_fields
            }
            cleaned = {key: value for key, value in cleaned.items() if value not in (None, "", [], {})}
            row = db.query(BrowserStorageSnapshotModel).filter(
                BrowserStorageSnapshotModel.BrowserId == payload.browser_id,
                BrowserStorageSnapshotModel.Category == category,
            ).first()

            if not cleaned:
                if row:
                    db.delete(row)
                continue

            encrypted = cipher.encrypt(json.dumps(cleaned, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("ascii")
            if row:
                row.UserId = (current_user or {}).get("sub")
                row.EncryptedJson = encrypted
                row.CapturedAt = now
                row.SourcePath = payload.source_path
            else:
                db.add(BrowserStorageSnapshotModel(
                    Id=str(uuid.uuid4()),
                    BrowserId=payload.browser_id,
                    UserId=(current_user or {}).get("sub"),
                    Category=category,
                    EncryptedJson=encrypted,
                    CapturedAt=now,
                    SourcePath=payload.source_path,
                ))
            saved += 1
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"savedCategories": saved, "capturedAt": now}


@router.delete("/browser-storage/{browser_id}")
def delete_browser_storage_snapshot(browser_id: str, db: Session = Depends(get_db)):
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,80}", browser_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid browser identifier")
    deleted = db.query(BrowserStorageSnapshotModel).filter(
        BrowserStorageSnapshotModel.BrowserId == browser_id
    ).delete(synchronize_session=False)
    db.commit()
    return {"deletedCategories": deleted}


@router.get("/admin/browser-storage")
def list_browser_storage_snapshots(
    _: dict = Depends(require_admin),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Only platform admins can read browser-storage records and decrypted values."""
    if category and category not in CATEGORY_FIELDS and category != "google_profile":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown browser data category")

    snapshot_query = db.query(BrowserStorageSnapshotModel)
    if category and category != "google_profile":
        snapshot_query = snapshot_query.filter(BrowserStorageSnapshotModel.Category == category)
    google_query = db.query(GoogleProfileConsentModel)
    include_google = category is None or category == "google_profile"
    include_snapshots = category != "google_profile"

    snapshot_total = snapshot_query.count() if include_snapshots else 0
    google_total = google_query.count() if include_google else 0
    total = snapshot_total + google_total
    category_counts = {
        item[0]: item[1]
        for item in db.query(BrowserStorageSnapshotModel.Category, func.count(BrowserStorageSnapshotModel.Id))
        .group_by(BrowserStorageSnapshotModel.Category).all()
    }
    category_counts["google_profile"] = google_total if category == "google_profile" else db.query(GoogleProfileConsentModel).count()

    fetch_count = offset + limit
    snapshot_rows = snapshot_query.order_by(
        BrowserStorageSnapshotModel.CapturedAt.desc()
    ).limit(fetch_count).all() if include_snapshots else []
    google_rows = google_query.order_by(
        GoogleProfileConsentModel.CapturedAt.desc()
    ).limit(fetch_count).all() if include_google else []
    cipher = _cipher()
    records = []

    def decrypt_json(encrypted_json: str) -> dict:
        try:
            return json.loads(cipher.decrypt(encrypted_json.encode("ascii")).decode("utf-8"))
        except (InvalidToken, ValueError, json.JSONDecodeError):
            return {"unavailable": "Data key changed or stored data is unreadable"}

    for row in snapshot_rows:
        records.append({
            "id": row.Id,
            "browserId": row.BrowserId,
            "userId": row.UserId,
            "category": row.Category,
            "data": _without_exact_coordinates(decrypt_json(row.EncryptedJson)),
            "capturedAt": row.CapturedAt,
            "sourcePath": row.SourcePath,
        })
    for row in google_rows:
        records.append({
            "id": row.GoogleSubjectHash,
            "browserId": "google:" + row.GoogleSubjectHash[:16],
            "userId": row.UserId,
            "category": "google_profile",
            "data": decrypt_json(row.EncryptedJson),
            "capturedAt": row.CapturedAt,
            "sourcePath": row.SourcePath,
        })
    records.sort(key=lambda record: record.get("capturedAt") or "", reverse=True)
    records = records[offset:offset + limit]
    return {
        "records": records,
        "count": len(records),
        "total": total,
        "offset": offset,
        "limit": limit,
        "categoryCounts": category_counts,
    }
