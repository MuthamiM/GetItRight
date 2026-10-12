import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.api.features.auth.models import UserModel
from backend.api.features.auth.schemas import LoginRequest, RegisterRequest, AuthResponse, UserOut
from backend.api.core.security import verify_password, get_password_hash, create_access_token

PLAN_META = {
    "free": {"name": "Civic Starter", "voters": 1000, "polls": 5, "url": "/console/admin.html"},
    "pro": {"name": "Civic Pro", "voters": 25000, "polls": 50, "url": "/console/admin.html"},
    "org": {"name": "Institutional Org", "voters": 100000, "polls": 200, "url": "/console/admin.html"},
    "election": {"name": "Sovereign Election Guard", "voters": 10000000, "polls": 1000, "url": "/console/admin.html"},
}


def _plain_text(value: Optional[str], field: str, maximum: int, required: bool = False) -> Optional[str]:
    clean = (value or "").strip()
    if not clean and not required:
        return None
    if not clean or len(clean) > maximum or any(char in clean for char in "<>"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} must be plain text")
    return clean

def authenticate_user(db: Session, creds: LoginRequest) -> AuthResponse:
    user = db.query(UserModel).filter(UserModel.Email == creds.email.strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. No user registered with this email."
        )

    if user.Status != "Active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is not active")

    if not verify_password(creds.password, user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password provided."
        )

    redirect_url = "/console/admin.html" if user.Role == "Admin" else "/pages/vote.html"
    if user.ConsoleUrl != redirect_url:
        user.ConsoleUrl = redirect_url
        db.commit()

    token = create_access_token({
        "sub": user.Id,
        "email": user.Email,
        "role": user.Role,
        "plan": user.Plan,
        "name": user.FullName,
        "tokenVersion": user.TokenVersion or 0,
    })

    user_out = UserOut(
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
        consoleUrl=redirect_url,
        isAdmin=(user.Role == "Admin")
    )

    return AuthResponse(
        success=True,
        token=token,
        user=user_out,
        redirectUrl=redirect_url,
        isAdmin=(user.Role == "Admin")
    )

def register_user(db: Session, data: RegisterRequest) -> AuthResponse:
    existing = db.query(UserModel).filter(UserModel.Email == data.email.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Public registration never grants paid plans or administrative access.
    # Plan changes must be approved through the protected administration API.
    plan_key = "free"
    meta = PLAN_META[plan_key]

    new_id = f"USR-{uuid.uuid4().hex[:6].upper()}"
    new_user = UserModel(
        Id=new_id,
        FullName=_plain_text(data.fullName, "Full name", 120, required=True),
        Email=data.email.strip(),
        Password=get_password_hash(data.password),
        PhoneNumber=_plain_text(data.phoneNumber, "Phone number", 30),
        IpAddress=None,
        Latitude=None,
        Longitude=None,
        DeviceDetails=None,
        Role="Customer",
        Plan=plan_key,
        PlanName=meta["name"],
        Organization=_plain_text(data.organization, "Organization", 200) or "Independent",
        CreatedAt=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        Status="Active",
        TotalPollsCreated=0,
        TotalVotesReceived=0,
        VoterQuota=meta["voters"],
        PollsQuota=meta["polls"],
        ConsoleUrl=meta["url"],
        LastLogin="Just now"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({
        "sub": new_user.Id,
        "email": new_user.Email,
        "role": new_user.Role,
        "plan": new_user.Plan,
        "name": new_user.FullName,
        "tokenVersion": new_user.TokenVersion or 0,
    })

    user_out = UserOut(
        id=new_user.Id,
        fullName=new_user.FullName,
        email=new_user.Email,
        phoneNumber=new_user.PhoneNumber,
        ipAddress=new_user.IpAddress,
        latitude=new_user.Latitude,
        longitude=new_user.Longitude,
        deviceDetails=new_user.DeviceDetails,
        role=new_user.Role,
        plan=new_user.Plan,
        planName=new_user.PlanName,
        organization=new_user.Organization,
        status=new_user.Status,
        voterQuota=new_user.VoterQuota,
        pollsQuota=new_user.PollsQuota,
        consoleUrl=new_user.ConsoleUrl,
        isAdmin=False
    )

    return AuthResponse(
        success=True,
        token=token,
        user=user_out,
        redirectUrl=new_user.ConsoleUrl,
        isAdmin=False
    )

def generate_email_otp(db: Session, email: str) -> dict:
    # No mail delivery provider is configured. Do not expose OTPs in an API
    # response or pretend delivery has occurred.
    return {
        "success": True,
        "message": "If the account exists, password recovery instructions will be sent when email delivery is configured."
    }

def verify_otp_and_reset_password(db: Session, email: str, otp: str, new_password: str) -> dict:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Password recovery is temporarily unavailable because secure email delivery is not configured."
    )

def reset_password_for_email(db: Session, email: str, new_password: str) -> dict:
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Use the OTP password recovery flow")

def change_user_password(db: Session, user_id: str, old_pass: str, new_pass: str) -> dict:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(old_pass, user.Password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect")
    user.Password = get_password_hash(new_pass.strip())
    user.TokenVersion = (user.TokenVersion or 0) + 1
    db.commit()
    return {"success": True, "message": "Password changed successfully"}

def update_user_profile(db: Session, user_id: str, full_name: Optional[str] = None, phone: Optional[str] = None, org: Optional[str] = None) -> UserOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if full_name and full_name.strip():
        user.FullName = _plain_text(full_name, "Full name", 120, required=True)
    if phone is not None:
        user.PhoneNumber = _plain_text(phone, "Phone number", 30)
    if org and org.strip():
        user.Organization = _plain_text(org, "Organization", 200)
    db.commit()
    db.refresh(user)
    redirect_url = "/console/admin.html"
    return UserOut(
        id=user.Id,
        fullName=user.FullName,
        email=user.Email,
        phoneNumber=user.PhoneNumber,
        ipAddress=user.IpAddress,
        latitude=user.Latitude,
        longitude=user.Longitude,
        deviceDetails=user.DeviceDetails,
        role=user.Role,
        plan=user.Plan,
        planName=user.PlanName,
        organization=user.Organization,
        status=user.Status,
        voterQuota=user.VoterQuota,
        pollsQuota=user.PollsQuota,
        consoleUrl=redirect_url,
        isAdmin=(user.Role == "Admin")
    )

def verify_user_token(db: Session, token_str: str) -> dict:
    from backend.api.core.security import decode_access_token
    payload = decode_access_token(token_str)
    if not payload:
        return {"valid": False, "user": None}
    user_id = payload.get("sub")
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user or user.Status != "Active" or payload.get("tokenVersion") != (user.TokenVersion or 0):
        return {"valid": False, "user": None}
    redirect_url = "/console/admin.html"
    user_out = UserOut(
        id=user.Id,
        fullName=user.FullName,
        email=user.Email,
        phoneNumber=user.PhoneNumber,
        ipAddress=user.IpAddress,
        latitude=user.Latitude,
        longitude=user.Longitude,
        deviceDetails=user.DeviceDetails,
        role=user.Role,
        plan=user.Plan,
        planName=user.PlanName,
        organization=user.Organization,
        status=user.Status,
        voterQuota=user.VoterQuota,
        pollsQuota=user.PollsQuota,
        consoleUrl=redirect_url,
        isAdmin=(user.Role == "Admin")
    )
    return {"valid": True, "user": user_out}


