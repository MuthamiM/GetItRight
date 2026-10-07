from typing import Optional
from pydantic import BaseModel

class UserDetailOut(BaseModel):
    id: str
    fullName: str
    email: str
    role: str
    plan: str
    planName: str
    organization: Optional[str] = "Independent"
    createdAt: str
    status: str
    totalPollsCreated: int
    totalVotesReceived: int
    voterQuota: int
    pollsQuota: int
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
