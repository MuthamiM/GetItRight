import hashlib
import json
import secrets
import urllib.parse
import urllib.request
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from backend.api.features.auth.models import PasswordRecoveryCodeModel, UserModel
from backend.api.core.config import settings
from backend.api.features.auth.schemas import LoginRequest, RegisterRequest, AuthResponse, UserOut
from backend.api.core.security import verify_password, get_password_hash, create_access_token
from backend.api.core.identity import normalize_email, normalize_phone

PLAN_META = {
    "free": {"name": "Starter", "voters": 1000, "polls": 5, "url": "/console/user.html"},
    "pro": {"name": "Pro", "voters": 25000, "polls": 50, "url": "/console/user.html"},
    "org": {"name": "Organization", "voters": 100000, "polls": 200, "url": "/console/user.html"},
    # Legacy tier retained only to keep existing account records readable.
    "election": {"name": "Sovereign Election Guard", "voters": 10000000, "polls": 1000, "url": "/console/user.html"},
}


def _plain_text(value: Optional[str], field: str, maximum: int, required: bool = False) -> Optional[str]:
    clean = (value or "").strip()
    if not clean and not required:
        return None
    if not clean or len(clean) > maximum or any(char in clean for char in "<>"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} must be plain text")
    return clean

def authenticate_user(db: Session, creds: LoginRequest) -> AuthResponse:
    user = db.query(UserModel).filter(func.lower(func.trim(UserModel.Email)) == normalize_email(creds.email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account exists."
        )

    if user.Status != "Active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is not active")

    if not verify_password(creds.password, user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password provided."
        )

    from backend.api.features.users.service import expire_user_plan_if_needed
    user = expire_user_plan_if_needed(db, user)

    is_admin = (user.Role in ["Admin", "Super Admin"])
    is_free = (not user.Plan or user.Plan.lower() == "free")

    if getattr(creds, "surface", None) == "web_console" and not is_admin and is_free:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free plan accounts cannot access the client web console. Please upgrade to a paid plan."
        )

    redirect_url = "/console/admin.html" if is_admin else ("/pricing.html" if is_free else "/console/user.html")
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

    is_admin = (user.Role in ["Admin", "Super Admin"])
    user_out = UserOut(
        id=user.Id,
        fullName=user.FullName,
        email=user.Email,
        phoneNumber=user.PhoneNumber,
        role=user.Role,
        plan=None if is_admin else user.Plan,
        planName=None if is_admin else user.PlanName,
        planExpiresAt=None if is_admin else user.PlanExpiresAt,
        organization=user.Organization,
        organizationContactRole=user.OrganizationContactRole,
        status=user.Status,
        voterQuota=None if is_admin else user.VoterQuota,
        pollsQuota=None if is_admin else user.PollsQuota,
        consoleUrl=redirect_url,
        isAdmin=is_admin
    )

    return AuthResponse(
        success=True,
        token=token,
        user=user_out,
        redirectUrl=redirect_url,
        isAdmin=is_admin
    )

def register_user(db: Session, data: RegisterRequest) -> AuthResponse:
    email = normalize_email(data.email)
    organization_plan_application = (data.plan or "free").strip().lower() == "org"
    organization = _plain_text(data.organization, "Organization name", 200, required=organization_plan_application)
    organization_contact_role = _plain_text(data.organizationContactRole, "Applying as", 100, required=organization_plan_application)
    email_domain = email.rsplit("@", 1)[-1].lower()
    if organization_plan_application and (email_domain == "gmail.com" or email_domain.endswith(".gmail.com")):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization plan applications require a business email address. Gmail addresses are not accepted.")
    phone = _plain_text(data.phoneNumber, "Phone number", 30)
    phone_canonical = normalize_phone(phone)
    if phone and not phone_canonical:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid phone number."
        )
    existing = db.query(UserModel).filter(func.lower(func.trim(UserModel.Email)) == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    if phone_canonical and db.query(UserModel.Id).filter(UserModel.PhoneCanonical == phone_canonical).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this phone number already exists."
        )

    # Public registration never grants paid plans or administrative access.
    # Plan changes must be approved through the protected administration API.
    plan_key = "free"
    meta = PLAN_META[plan_key]

    new_id = f"USR-{uuid.uuid4().hex[:6].upper()}"
    new_user = UserModel(
        Id=new_id,
        FullName=_plain_text(data.fullName, "Full name", 120, required=True),
        Email=email,
        Password=get_password_hash(data.password),
        PhoneNumber=phone,
        PhoneCanonical=phone_canonical,
        IpAddress=None,
        Latitude=None,
        Longitude=None,
        DeviceDetails=None,
        Role="Customer",
        Plan=plan_key,
        PlanName=meta["name"],
        Organization=organization or "Independent",
        OrganizationContactRole=organization_contact_role,
        CreatedAt=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        Status="Active",
        TotalPollsCreated=0,
        TotalVotesReceived=0,
        VoterQuota=meta["voters"],
        PollsQuota=meta["polls"],
        ConsoleUrl=meta["url"],
        LastLogin="Just now"
    )

    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address or phone number already exists."
        )
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
        planExpiresAt=new_user.PlanExpiresAt,
        organization=new_user.Organization,
        organizationContactRole=new_user.OrganizationContactRole,
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
    user = db.query(UserModel).filter(func.lower(func.trim(UserModel.Email)) == normalize_email(email)).first()
    generic = "If the account exists, a recovery code has been sent to its email address."
    if not user or not settings.RESEND_API_KEY:
        return {"success": True, "message": generic}

    now = datetime.now(timezone.utc)
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.query(PasswordRecoveryCodeModel).filter(
        PasswordRecoveryCodeModel.UserId == user.Id,
        PasswordRecoveryCodeModel.UsedAt.is_(None),
    ).update({"UsedAt": now})
    db.add(PasswordRecoveryCodeModel(
        Id=str(uuid.uuid4()),
        UserId=user.Id,
        CodeHash=hashlib.sha256(code.encode()).hexdigest(),
        ExpiresAt=now + timedelta(minutes=10),
        CreatedAt=now,
    ))
    db.commit()
    reset_link = (
        f"{settings.PASSWORD_RESET_URL}?email={urllib.parse.quote(user.Email)}"
        f"&otp={urllib.parse.quote(code)}"
    )
    payload = json.dumps({
        "from": settings.RESEND_FROM_EMAIL,
        "to": [settings.RESEND_TEST_RECIPIENT or user.Email],
        "subject": "IcapsQ password recovery code",
        "text": (
            "Use this link to update your IcapsQ password:\n\n"
            f"{reset_link}\n\n"
            f"If the link does not open, use recovery code {code}. It expires in 10 minutes."
        ),
        "html": (
            "<p>Use the button below to update your IcapsQ password.</p>"
            f'<p><a href="{reset_link}">Update your password</a></p>'
            f"<p>This link expires in 10 minutes. Your recovery code is {code}.</p>"
        ),
    }).encode()
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "IcapsQ/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10):
            return {"success": True, "message": generic}
    except Exception as error:
        db.query(PasswordRecoveryCodeModel).filter(
            PasswordRecoveryCodeModel.UserId == user.Id,
            PasswordRecoveryCodeModel.CodeHash == hashlib.sha256(code.encode()).hexdigest(),
        ).update({"UsedAt": datetime.now(timezone.utc)})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery email could not be sent. Please try again later.",
        ) from error

def verify_otp_and_reset_password(db: Session, email: str, otp: str, new_password: str) -> dict:
    user = db.query(UserModel).filter(func.lower(func.trim(UserModel.Email)) == normalize_email(email)).first()
    now = datetime.now(timezone.utc)
    recovery = db.query(PasswordRecoveryCodeModel).filter(
        PasswordRecoveryCodeModel.UserId == (user.Id if user else ""),
        PasswordRecoveryCodeModel.UsedAt.is_(None),
        PasswordRecoveryCodeModel.ExpiresAt > now,
    ).order_by(PasswordRecoveryCodeModel.CreatedAt.desc()).first()
    if not recovery or not secrets.compare_digest(recovery.CodeHash, hashlib.sha256(otp.strip().encode()).hexdigest()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired recovery code.")
    user.Password = get_password_hash(new_password.strip())
    user.TokenVersion = (user.TokenVersion or 0) + 1
    recovery.UsedAt = now
    db.commit()
    return {"success": True, "message": "Password reset successfully. You can now sign in."}

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
    if full_name and full_name.strip() and full_name.strip() != user.FullName:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be changed after account creation."
        )
    if phone is not None:
        normalized_phone = _plain_text(phone, "Phone number", 30)
        phone_canonical = normalize_phone(normalized_phone)
        if normalized_phone and not phone_canonical:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Enter a valid phone number."
            )
        duplicate_phone = db.query(UserModel.Id).filter(
            UserModel.PhoneCanonical == phone_canonical,
            UserModel.Id != user.Id,
        ).first() if phone_canonical else None
        if duplicate_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this phone number already exists."
            )
        user.PhoneNumber = normalized_phone
        user.PhoneCanonical = phone_canonical
    if org and org.strip():
        user.Organization = _plain_text(org, "Organization", 200)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this phone number already exists."
        )
    db.refresh(user)
    redirect_url = "/console/admin.html" if user.Role in ["Admin", "Super Admin"] else user.ConsoleUrl
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
        organizationContactRole=user.OrganizationContactRole,
        status=user.Status,
        voterQuota=user.VoterQuota,
        pollsQuota=user.PollsQuota,
        consoleUrl=redirect_url,
        isAdmin=(user.Role in ["Admin", "Super Admin"])
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
    redirect_url = "/console/admin.html" if user.Role in ["Admin", "Super Admin"] else user.ConsoleUrl
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
        organizationContactRole=user.OrganizationContactRole,
        status=user.Status,
        voterQuota=user.VoterQuota,
        pollsQuota=user.PollsQuota,
        consoleUrl=redirect_url,
        isAdmin=(user.Role in ["Admin", "Super Admin"])
    )
    return {"valid": True, "user": user_out}
