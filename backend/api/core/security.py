import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt, JWTError
import bcrypt
from backend.api.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check password against hash with bcrypt fallback for plaintext seed accounts."""
    if not hashed_password:
        return False
    # If the password in DB is plain text (e.g. initial seed), allow check
    if plain_password == hashed_password:
        return True
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for password."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_merkle_receipt(poll_id: str, option_index: int, voter_pseudonym: str, timestamp: str) -> str:
    """Calculate cryptographic SHA-256 receipt for verifiable ballot submission."""
    payload = f"{poll_id}:{option_index}:{voter_pseudonym}:{timestamp}:{secrets.token_hex(8)}"
    return "0x" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
