from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: str
    password: str
    ipAddress: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deviceDetails: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str
    newPassword: Optional[str] = None

class RequestOTPRequest(BaseModel):
    email: str

class VerifyOTPResetRequest(BaseModel):
    email: str
    otp: str
    newPassword: str

class RegisterRequest(BaseModel):
    fullName: str
    email: str
    password: str
    phoneNumber: Optional[str] = None
    organization: Optional[str] = "Independent"
    plan: Optional[str] = "free"
    ipAddress: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deviceDetails: Optional[str] = None

class UserOut(BaseModel):
    id: str
    fullName: str
    email: str
    phoneNumber: Optional[str] = None
    ipAddress: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deviceDetails: Optional[str] = None
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
