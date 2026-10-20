from typing import Optional
from pydantic import BaseModel

class UserDetailOut(BaseModel):
    id: str
    fullName: str
    email: str
    phoneNumber: Optional[str] = None
    role: str
    plan: Optional[str] = None
    planName: Optional[str] = None
    organization: Optional[str] = "Independent"
    createdAt: str
    status: str
    totalPollsCreated: int
    totalVotesReceived: int
    voterQuota: Optional[int] = None
    pollsQuota: Optional[int] = None
    consoleUrl: str
    lastLogin: Optional[str] = None
    isAdmin: bool = False

class CreateUserRequest(BaseModel):
    fullName: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: str
    password: str
    plan: Optional[str] = "free"
    organization: Optional[str] = "Independent"
    role: Optional[str] = "Customer"

class UpdateUserStatusRequest(BaseModel):
    status: str

class UpdateUserPlanRequest(BaseModel):
    plan: str
    phoneNumber: Optional[str] = None

class UpdateUserRoleRequest(BaseModel):
    role: str

class RoleOut(BaseModel):
    id: str
    name: str
    description: str
    isSystem: bool = False
    permissions: list[str] = []

class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    permissions: Optional[list[str]] = []

# Legacy alias
UserStatusUpdate = UpdateUserStatusRequest
