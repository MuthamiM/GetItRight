from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.api.core.database import get_db
from backend.api.features.auth.schemas import LoginRequest, RegisterRequest, AuthResponse, UserOut, ForgotPasswordRequest, RequestOTPRequest, VerifyOTPResetRequest
from backend.api.features.auth.service import authenticate_user, register_user, reset_password_for_email, generate_email_otp, verify_otp_and_reset_password
from backend.api.features.auth.models import UserModel
from backend.api.middleware.auth_middleware import get_current_user_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=AuthResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    return authenticate_user(db, creds)

from fastapi import APIRouter, Depends, HTTPException, status, Request

@router.post("/register", response_model=AuthResponse)
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "Browser/Mobile")
    if not data.ipAddress:
        data.ipAddress = client_ip
    if not data.deviceDetails:
        data.deviceDetails = user_agent
    return register_user(db, data)

@router.post("/send-otp")
def request_otp(data: RequestOTPRequest, db: Session = Depends(get_db)):
    return generate_email_otp(db, data.email)

@router.post("/verify-otp-reset")
def verify_otp_reset(data: VerifyOTPResetRequest, db: Session = Depends(get_db)):
    return verify_otp_and_reset_password(db, data.email, data.otp, data.newPassword)

@router.post("/reset-password")
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return reset_password_for_email(db, data.email, data.newPassword)

@router.get("/me", response_model=UserOut)
def get_current_profile(token_data: dict = Depends(get_current_user_token), db: Session = Depends(get_db)):
    user_id = token_data.get("sub")
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    redirect_url = "/console/dashboard.html" if user.Role == "Admin" else user.ConsoleUrl
    return UserOut(
        id=user.Id,
        fullName=user.FullName,
        email=user.Email,
        role=user.Role,
        plan=user.Plan,
        planName=user.PlanName,
        organization=user.Organization,
        status=user.Status,
        voterQuota=user.VoterQuota,
        pollsQuota=user.PollsQuota,
        consoleUrl=redirect_url
    )

@router.post("/logout")
def logout():
    return {"success": True, "message": "Logged out successfully"}
