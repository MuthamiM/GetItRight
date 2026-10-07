from datetime import datetime, timezone
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.api.features.auth.models import UserModel
from backend.api.features.users.schemas import UserDetailOut, UserStatusUpdate, CreateUserRequest, UpdateUserPlanRequest
from backend.api.core.security import get_password_hash

PLAN_METADATA = {
    "free": {"name": "Civic Starter", "voters": 1000, "polls": 5, "url": "/console/community.html"},
    "pro": {"name": "Civic Pro", "voters": 25000, "polls": 50, "url": "/console/pro.html"},
    "org": {"name": "Institutional Org", "voters": 100000, "polls": 200, "url": "/console/organization.html"},
    "election": {"name": "Sovereign Election Guard", "voters": 10000000, "polls": 1000, "url": "/console/election.html"},
}

# Map full plan names to canonical short keys
_PLAN_NAME_TO_KEY = {v["name"].lower(): k for k, v in PLAN_METADATA.items()}

def resolve_plan_key(raw: str) -> str:
    """Accept 'pro', 'Civic Pro', 'civic pro', etc. and return canonical key."""
    key = raw.strip().lower()
    if key in PLAN_METADATA:
        return key
    return _PLAN_NAME_TO_KEY.get(key, "free")

def map_user(u: UserModel) -> UserDetailOut:
    redirect_url = "/console/dashboard.html" if u.Role == "Admin" else u.ConsoleUrl
    return UserDetailOut(
        id=u.Id,
        fullName=u.FullName,
        email=u.Email,
        role=u.Role,
        plan=u.Plan,
        planName=u.PlanName,
        organization=u.Organization,
        createdAt=u.CreatedAt,
        status=u.Status,
        totalPollsCreated=u.TotalPollsCreated,
        totalVotesReceived=u.TotalVotesReceived,
        voterQuota=u.VoterQuota,
        pollsQuota=u.PollsQuota,
        consoleUrl=redirect_url,
        lastLogin=u.LastLogin,
        isAdmin=(u.Role == "Admin")
    )

def list_users(db: Session, plan: Optional[str] = None) -> List[UserDetailOut]:
    query = db.query(UserModel)
    if plan:
        query = query.filter(UserModel.Plan == plan.lower())
    users = query.all()
    return [map_user(u) for u in users]

def get_user_by_id(db: Session, user_id: str) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return map_user(user)

def create_user(db: Session, req: CreateUserRequest) -> UserDetailOut:
    effective_name = (req.fullName or req.name or req.full_name or "").strip()
    if not req.email or not effective_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and Full Name are required.")

    existing = db.query(UserModel).filter(UserModel.Email == req.email.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")

    if req.role and req.role.lower() == "admin":
        existing_admin = db.query(UserModel).filter(UserModel.Role == "Admin").first()
        if existing_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Security policy violation: Only ONE Admin account is permitted in the platform.")

    plan_key = resolve_plan_key(req.plan or "free")
    meta = PLAN_METADATA[plan_key]
    new_id = f"USR-{uuid.uuid4().hex[:6].upper()}"

    user = UserModel(
        Id=new_id,
        FullName=effective_name,
        Email=req.email.strip().lower(),
        Password=get_password_hash(req.password),
        Role="Customer" if not req.role or req.role.lower() != "admin" else "Admin",
        Plan=plan_key,
        PlanName=meta["name"],
        Organization=req.organization.strip() if req.organization else "Independent",
        CreatedAt=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        Status="Active",
        TotalPollsCreated=0,
        TotalVotesReceived=0,
        VoterQuota=meta["voters"],
        PollsQuota=meta["polls"],
        ConsoleUrl=meta["url"],
        LastLogin="Just now"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return map_user(user)

def update_user_status(db: Session, user_id: str, update_data: UserStatusUpdate) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    if user.Role == "Admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify the primary Admin status.")
    user.Status = update_data.status
    db.commit()
    db.refresh(user)
    return map_user(user)

def update_user_plan(db: Session, user_id: str, req: UpdateUserPlanRequest) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    plan_key = resolve_plan_key(req.plan)
    meta = PLAN_METADATA[plan_key]
    user.Plan = plan_key
    user.PlanName = meta["name"]
    user.ConsoleUrl = meta["url"]
    user.VoterQuota = meta["voters"]
    user.PollsQuota = meta["polls"]
    db.commit()
    db.refresh(user)
    return map_user(user)

SYSTEM_ROLES = [
    {
        "id": "ROLE-ADMIN",
        "name": "Admin",
        "description": "Primary Platform Administrator with full access to encryption keys and security control.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey", "open_input_fields", "manage_users", "manage_roles", "audit_merkle", "export_data"]
    },
    {
        "id": "ROLE-ANALYST",
        "name": "Analyst",
        "description": "Data Analyst with real-time chart insights and report generation access.",
        "isSystem": True,
        "permissions": ["view_analytics", "export_data", "audit_merkle"]
    },
    {
        "id": "ROLE-AUDITOR",
        "name": "Auditor",
        "description": "Independent Security & Merkle Ledger Auditor.",
        "isSystem": True,
        "permissions": ["audit_merkle", "view_checkpoint_ledger"]
    },
    {
        "id": "ROLE-ENTERPRISE",
        "name": "Enterprise Publisher",
        "description": "Enterprise Organization author with open input field surveys and custom quota.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey", "open_input_fields", "export_data"]
    },
    {
        "id": "ROLE-PRO",
        "name": "Civic Pro",
        "description": "Verified Civic Publisher with expanded voting quota.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey", "open_input_fields"]
    },
    {
        "id": "ROLE-CUSTOMER",
        "name": "Customer",
        "description": "Standard polling and survey user.",
        "isSystem": True,
        "permissions": ["create_poll", "create_survey"]
    }
]

CUSTOM_ROLES = []

def list_roles():
    return SYSTEM_ROLES + CUSTOM_ROLES

def create_role(req):
    role_id = f"ROLE-CUST-{uuid.uuid4().hex[:4].upper()}"
    new_role = {
        "id": role_id,
        "name": req.name.strip(),
        "description": (req.description or "").strip(),
        "isSystem": False,
        "permissions": req.permissions or ["create_poll", "create_survey"]
    }
    CUSTOM_ROLES.append(new_role)
    return new_role

def update_user_role(db: Session, user_id: str, req) -> UserDetailOut:
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    user.Role = req.role
    db.commit()
    db.refresh(user)
    return map_user(user)
