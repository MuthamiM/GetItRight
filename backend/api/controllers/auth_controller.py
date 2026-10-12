from sqlalchemy.orm import Session
from starlette.requests import Request
from backend.api.features.auth.schemas import (
    LoginRequest, AuthResponse, RegisterRequest,
    RequestOTPRequest, VerifyOTPResetRequest, ForgotPasswordRequest
)
from backend.api.features.auth import service as auth_service

class AuthController:
    """Controller for user authentication, token issuance, and credential recovery."""

    @staticmethod
    def login(db: Session, creds: LoginRequest) -> AuthResponse:
        return auth_service.authenticate_user(db, creds)

    @staticmethod
    def register(db: Session, data: RegisterRequest, request: Request) -> AuthResponse:
        return auth_service.register_user(db, data, request)

    @staticmethod
    def request_otp(db: Session, data: RequestOTPRequest):
        return auth_service.generate_otp(db, data)

    @staticmethod
    def verify_otp_reset(db: Session, data: VerifyOTPResetRequest):
        return auth_service.verify_otp_and_reset(db, data)

    @staticmethod
    def forgot_password(db: Session, data: ForgotPasswordRequest):
        return auth_service.reset_password(db, data)

    @staticmethod
    def verify_token(db: Session, token: str):
        return auth_service.verify_access_token(db, token)

    @staticmethod
    def get_current_profile(db: Session, token_data: dict):
        return auth_service.get_user_profile(db, token_data)
