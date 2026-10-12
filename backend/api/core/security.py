import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from backend.api.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a bcrypt password hash without accepting legacy plaintext values."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for password."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.now(timezone.utc)
    payload = data.copy()
    payload.update({
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        "jti": secrets.token_urlsafe(18),
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
    except JWTError:
        return None

def generate_merkle_receipt(poll_id: str, option_index: int, voter_pseudonym: str, timestamp: str) -> str:
    """Calculate cryptographic SHA-256 receipt for verifiable ballot submission."""
    payload = f"{poll_id}:{option_index}:{voter_pseudonym}:{timestamp}:{secrets.token_hex(32)}"
    return "0x" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
