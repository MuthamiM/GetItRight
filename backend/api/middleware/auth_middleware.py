from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.api.core.database import get_db
from backend.api.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def _authenticate(token: str, db: Session) -> dict:
    # Import here so middleware package initialization does not recursively
    # initialize the features package and its route modules.
    from backend.api.features.auth.models import UserModel

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")

    user = db.query(UserModel).filter(UserModel.Id == payload["sub"]).first()
    if not user or user.Status != "Active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is unavailable")
    if payload.get("tokenVersion") != (user.TokenVersion or 0):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked")

    # Claims that can change are resolved from the database for every request.
    payload.update({"role": user.Role, "plan": user.Plan, "name": user.FullName})
    return payload


def get_current_user_token(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _authenticate(token, db)


def get_optional_current_user_token(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[dict]:
    return _authenticate(token, db) if token else None

def require_admin(payload: dict = Depends(get_current_user_token)) -> dict:
    role = payload.get("role")
    if role not in ["Admin", "Super Admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator authorization required")
    return payload
