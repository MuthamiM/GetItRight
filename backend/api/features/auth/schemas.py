from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


def validate_password(value: str) -> str:
    if len(value) < 12 or not any(c.islower() for c in value) or not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("Password must be at least 12 characters and include upper-case, lower-case, and numeric characters")
    return value

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    ipAddress: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deviceDetails: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    newPassword: Optional[str] = None

class RequestOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPResetRequest(BaseModel):
    email: EmailStr
    otp: str
    newPassword: str

    _password_strength = field_validator("newPassword")(validate_password)

class RegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    password: str
    phoneNumber: Optional[str] = None
    organization: Optional[str] = "Independent"
    plan: Optional[str] = "free"
    ipAddress: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deviceDetails: Optional[str] = None

    _password_strength = field_validator("password")(validate_password)

class UserOut(BaseModel):
    id: str
    fullName: str
    email: str
    role: str
    plan: str
    planName: str
    organization: Optional[str] = "Independent"
    status: str
    voterQuota: int
    pollsQuota: int
    consoleUrl: str
    isAdmin: bool = False

class AuthResponse(BaseModel):
    success: bool
    token: str
    user: UserOut
    redirectUrl: str
    isAdmin: bool = False

class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str

    _password_strength = field_validator("newPassword")(validate_password)

class UpdateProfileRequest(BaseModel):
    fullName: Optional[str] = None
    phoneNumber: Optional[str] = None
    organization: Optional[str] = None

class VerifyTokenRequest(BaseModel):
    token: str

class VerifyTokenResponse(BaseModel):
    valid: bool
    user: Optional[UserOut] = None
