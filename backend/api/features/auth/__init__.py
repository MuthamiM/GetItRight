"""
Authentication and Role-Based Access Control Feature.
"""

from backend.api.features.auth.models import UserModel
from backend.api.features.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    UserOut
)
from backend.api.features.auth.service import authenticate_user, register_user
from backend.api.features.auth.routes import router

__all__ = [
    "UserModel",
    "LoginRequest",
    "RegisterRequest",
    "AuthResponse",
    "UserOut",
    "authenticate_user",
    "register_user",
    "router"
]
